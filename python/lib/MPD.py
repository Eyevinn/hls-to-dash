import tempfile
import re
import m3u8
import time
import datetime
import pycurl
from ffprobe import FFProbe
from lib import util
from lib import MPDAdaptationSet
from lib import MPDRepresentation
from lib import TS
import debug

class Period:
    def __init__(self, periodid):
        self.id = periodid
        self.periodStart = 0
        self.periodDuration = 30
        self.as_video = None
        self.as_audio = None
    def increaseDuration(self, duration):
        self.periodDuration += duration
    def addAdaptationSetVideo(self, as_video):
        self.as_video = as_video
    def haveAdaptationSetVideo(self):
        return self.as_video != None
    def getAdaptationSetVideo(self):
        return self.as_video
    def addAdaptationSetAudio(self, as_audio):
        self.as_audio = as_audio
    def haveAdaptationSetAudio(self):
        return self.as_audio != None
    def getAdaptationSetAudio(self):
        return self.as_audio
    def asXML(self):
        xml = '  <Period id="%s" start="%s">\n' % (self.id, util.PT(self.periodStart))
        xml += self.as_video.asXML()
        xml += self.as_audio.asXML()
        xml += '  </Period>\n'
        return xml

class Base:
    def __init__(self):
        self.maxSegmentDuration = 10
        self.startTime = 0
        self.periods = []
        period = Period('1')
        self.periods.append(period)
    def havePeriods(self):
        return len(self.periods) > 0
    def getPeriod(self, idx):
        return self.periods[idx]
    def asXML(self):
        xml = '<?xml version="1.0"?>';
        xml += '<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" profiles="urn:mpeg:dash:profile:isoff-live:2011" type="dynamic" minimumUpdatePeriod="PT10S" minBufferTime="PT1.500S" maxSegmentDuration="%s" availabilityStartTime="%s" publishTime="%s">\n' % (util.PT(self.maxSegmentDuration), self._getAvailabilityStartTime(), self._getPublishTime())
        if self.havePeriods():
            xml += self.getPeriod(0).asXML()
        xml += '</MPD>\n'
        return xml
    def _getAvailabilityStartTime(self):
        tsnow = time.time()
        availstart = tsnow - self.startTime
        return datetime.datetime.fromtimestamp(availstart).isoformat() + "Z"
    def _getPublishTime(self):
        return datetime.datetime.utcnow().isoformat() + "Z"
 

class HLS(Base):
    def __init__(self, playlistlocator):
        Base.__init__(self)
        self.playlistlocator = playlistlocator
        self.profilepattern = 'master(\d+).m3u8'
        self.numberpattern = 'master\d+_(\d+).ts'
        self.isRemote = False
        self.baseurl = ''
        res = re.match('^(.*)/.*.m3u8$', playlistlocator)
        if res:
            self.baseurl = res.group(1) + '/'
	if re.match('^http', playlistlocator):
            self.isRemote = True

    def setProfilePattern(self, profilepattern):
        self.profilepattern = profilepatten

    def load(self):
        debug.log("Loading playlist: ", self.playlistlocator)
        m3u8_obj = m3u8.load(self.playlistlocator)
        if m3u8_obj.is_variant:
            if m3u8_obj.playlist_type == "VOD":
                raise Exception("VOD playlists not yet supported")
            self._parseMaster(m3u8_obj)
        else:
            raise Exception("Can only create DASH manifest from an HLS master playlist")
        p = m3u8_obj.playlists[0]
        debug.log("Loading playlist: ", self.baseurl + p.uri)
        self._parsePlaylist(m3u8.load(self.baseurl + p.uri))
        debug.log("Audio: ", self.getPeriod(0).as_audio)
        debug.log("Video: ", self.getPeriod(0).as_video)

    def _profileFromFilename(self, filename):
        result = re.match(self.profilepattern, filename)
        if result:
            return result.group(1)
        else:
            return len(self.representations)

    def _getStartNumberFromFilename(self, filename):
        result = re.match(self.numberpattern, filename)
        if result:
            return result.group(1)
        return 0

    def _parsePlaylist(self, playlist):
        self.maxSegmentDuration = playlist.target_duration
        isFirst = True
        for seg in playlist.segments:
            #debug_print(vars(seg))
            duration = float(seg.duration)
            videoseg = MPDRepresentation.Segment(duration, isFirst)
            audioseg = MPDRepresentation.Segment(duration, isFirst)
            self.getPeriod(0).getAdaptationSetVideo().addSegment(videoseg)
            self.getPeriod(0).getAdaptationSetAudio().addSegment(audioseg)
            self.getPeriod(0).increaseDuration(int(duration))
            if isFirst:
                self.startTime = self._getStartTimeFromFile(seg.uri)
                videoseg.setStartTime(self.startTime)
                audioseg.setStartTime(self.startTime)
                as_audio = self.getPeriod(0).getAdaptationSetAudio()
                as_video = self.getPeriod(0).getAdaptationSetVideo()
                as_video.setStartNumber(self._getStartNumberFromFilename(seg.uri))
                as_video.setStartTime(self.startTime)
                as_audio.setStartNumber(self._getStartNumberFromFilename(seg.uri))
                as_audio.setStartTime(self.startTime)
            isFirst = False
    
    def _getStartTimeFromFile(self, uri):
        if self.isRemote:
            if not re.match('^http', uri):
                uri = self.baseurl + uri
            ts = TS.Remote(uri)
        else:
            ts = TS.Local(uri)
        ts.probe()
        return ts.getStartTime()
        
    def _parseMaster(self, variant):
        debug.log("Parsing master playlist")
        for playlist in variant.playlists:
            stream = playlist.stream_info
            (video_codec, audio_codec) = stream.codecs.split(',')
            profile = self._profileFromFilename(playlist.uri) 
            if not self.getPeriod(0).haveAdaptationSetVideo():
                as_video = MPDAdaptationSet.Video('video/mp4', video_codec) 
                self.getPeriod(0).addAdaptationSetVideo(as_video)
            if not self.getPeriod(0).haveAdaptationSetAudio():
                as_audio = MPDAdaptationSet.Audio('audio/mp4', audio_codec) 
                audio_representation = MPDRepresentation.Audio('audio-%s' % profile, 96000)
                as_audio.addRepresentation(audio_representation)
                self.getPeriod(0).addAdaptationSetAudio(as_audio)
            video_representation = MPDRepresentation.Video('video-%s' % profile, stream.bandwidth, stream.resolution[0], stream.resolution[1])
            self.getPeriod(0).getAdaptationSetVideo().addRepresentation(video_representation)


