import tempfile
import re
import m3u8
import time
import datetime
import pycurl
import os
from ffprobe import FFProbe
from lib import util
from lib import MPDAdaptationSet
from lib import MPDRepresentation
from lib import TS
import debug

class Period:
    def __init__(self, periodid):
        self.id = periodid
        self.periodStart = 0.0
        self.periodDuration = 0.0
        self.as_video = None
        self.as_audio = None
        self.eventstream = []
        self.isLastPeriod = False
    def setPeriodStart(self, start):
        self.periodStart = start
    def setPeriodId(self, periodid):
        self.id = periodid
    def getPeriodId(self):
        return self.id
    def increaseDuration(self, duration):
        self.periodDuration += duration
    def setAsLastPeriod(self):
        self.isLastPeriod = True
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
    def addSCTE35Splice(self, id, duration, scte35):
        event = SCTE35Event(id, int(duration), scte35)
        self.eventstream.append(event)
    def asXML(self):
        xml = '  <Period id="%s" start="%s">\n' % (self.id, util.PT(self.periodStart))
        if len(self.eventstream) > 0:
            timescale = self.eventstream[0].getTimescale()
            xml += '    <EventStream timescale="%d" schemeIdUri="urn:scte:scte35:2014:xml+bin">\n' % timescale
            for ev in self.eventstream:
                xml += ev.asXML()
            xml += '    </EventStream>\n'
        xml += self.as_video.asXML()
        xml += self.as_audio.asXML()
        xml += '  </Period>\n'
        return xml

class PeriodEvent:
    def __init__(self, id, duration):
        self.duration = duration
        self.id = id
        self.timescale = 90000
    def getTimescale(self):
        return self.timescale
    def getId(self):
        return self.id

class SCTE35Event(PeriodEvent):
    def __init__(self, id, duration, scte35):
        PeriodEvent.__init__(self, id, duration)
        self.scte35 = scte35
    def asXML(self):
        xml = '      <Event duration="%d" id="%d">\n' % (self.timescale * self.duration, self.getId())
        xml += '       <scte35:Signal>\n'
        xml += '         <scte35:Binary>\n'
        xml += '           %s\n' % self.scte35 
        xml += '         </scte35:Binary>\n'
        xml += '       </scte35:Signal>\n'
        xml += '      </Event>\n'
        return xml

class Base:
    def __init__(self):
        self.maxSegmentDuration = 10
        self.firstSegmentStartTime = 0
        self.periods = []
        period = Period('1')
        period.setPeriodStart(0.0)
        self.appendPeriod(period)
    def havePeriods(self):
        return len(self.periods) > 0
    def getPeriod(self, idx):
        return self.periods[idx]
    def getAllPeriods(self):
        return self.periods;
    def appendPeriod(self, period):
        self.periods.append(period)
    def asXML(self):
        xml = '<?xml version="1.0"?>';
        xml += '<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" profiles="urn:mpeg:dash:profile:isoff-live:2011" type="dynamic" minimumUpdatePeriod="PT10S" minBufferTime="PT1.500S" maxSegmentDuration="%s" availabilityStartTime="%s" publishTime="%s">\n' % (util.PT(self.maxSegmentDuration), self._getAvailabilityStartTime(), self._getPublishTime())
        if self.havePeriods():
            for p in self.getAllPeriods():
                xml += p.asXML()
        xml += '</MPD>\n'
        return xml
    def _getAvailabilityStartTime(self):
        tsnow = time.time()
        availstart = tsnow - self.firstSegmentStartTime
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
        self.currentPeriodIdx = 0
        self.profiles = []
        self.ctx = '/tmp/test.ctx'

        # Below should be set outside of this class
        self.splitperiod = True

        # Set last period id as default period id for first period
        if self.splitperiod == True:
            firstperiod = self.getPeriod(0)
            if os.path.isfile(self.ctx):
                with open(self.ctx, 'r+') as f:
                    periodid = f.read()
                    firstperiod.setPeriodId(periodid)          

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
        for per in self.getAllPeriods():
            debug.log("Audio: ", per.as_audio)
            debug.log("Video: ", per.as_video)

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
        doSplit = False
        eventid = 1
        offset = 0.0
        state = 'initial'
        isFirstSplit = True
        lastnumber = None
        for seg in playlist.segments:
            if state == 'initial':
                if seg.cue_out == True:
                    state = 'insidecue'
                else:
                    state = 'outsidecue'
            elif state == 'outsidecue':
                if seg.cue_out == True:
                    state = 'insidecue'
                    if not isFirst:
                        doSplit = True
            elif state == 'insidecue':
                if seg.cue_out == False:
                    state = 'outsidecue'
                    if not isFirst:
                        doSplit = True
            debug.log("[%s][P%d]: %s" % (state, self.currentPeriodIdx, seg.uri))

            if self.splitperiod and doSplit:
                debug.log("-- Split period before %s" % seg.uri)
                if isFirstSplit == True:
                    period = self.getPeriod(self.currentPeriodIdx)
                    period.setPeriodId("P%s" % lastnumber)
                    isFirstSplit = False
                self.currentPeriodIdx = self.currentPeriodIdx + 1
                newperiod = Period("P%s" % self._getStartNumberFromFilename(seg.uri))
                self._initiatePeriod(newperiod, self.profiles)
                self.appendPeriod(newperiod)
                isFirst = True
                doSplit = False
            duration = float(seg.duration)
            videoseg = MPDRepresentation.Segment(duration, isFirst)
            audioseg = MPDRepresentation.Segment(duration, isFirst)
            period = self.getPeriod(self.currentPeriodIdx)
            period.getAdaptationSetVideo().addSegment(videoseg)
            period.getAdaptationSetAudio().addSegment(audioseg)
            period.increaseDuration(duration)
            offset += duration
            if isFirst:
                if state == 'insidecue' and seg.cue_out == True:
                    debug.log("SCTE35:%s" % seg.scte35)
                    period.addSCTE35Splice(eventid, seg.scte35_duration, seg.scte35)
                    eventid = eventid + 1
                self.firstSegmentStartTime = self._getStartTimeFromFile(self.baseurl + seg.uri)
                videoseg.setStartTime(self.firstSegmentStartTime)
                audioseg.setStartTime(self.firstSegmentStartTime)
                period.setPeriodStart(self.firstSegmentStartTime)
                as_audio = period.getAdaptationSetAudio()
                as_video = period.getAdaptationSetVideo()
                as_video.setStartNumber(self._getStartNumberFromFilename(seg.uri))
                as_video.setStartTime(self.firstSegmentStartTime)
                as_audio.setStartNumber(self._getStartNumberFromFilename(seg.uri))
                as_audio.setStartTime(self.firstSegmentStartTime)
            isFirst = False
            lastnumber = self._getStartNumberFromFilename(seg.uri)
        allperiods = self.getAllPeriods()
        lastperiod = allperiods[len(allperiods)-1]
        lastperiod.setAsLastPeriod()
        with open(self.ctx, 'w+') as f:
            f.seek(0)
            f.write(lastperiod.getPeriodId())
            f.truncate()
    
    def _getStartTimeFromFile(self, uri):
        if self.isRemote:
            if not re.match('^http', uri):
                uri = self.baseurl + uri
            ts = TS.Remote(uri)
        else:
            ts = TS.Local(uri)
        ts.probe()
        return ts.getStartTime()

    def _initiatePeriod(self, period, profiles):
        for p in profiles:
            if not period.haveAdaptationSetVideo():
                as_video = MPDAdaptationSet.Video('video/mp4', p['videocodec']) 
                period.addAdaptationSetVideo(as_video)
            if not period.haveAdaptationSetAudio():
                as_audio = MPDAdaptationSet.Audio('audio/mp4', p['audiocodec']) 
                audio_representation = MPDRepresentation.Audio('audio-%s' % p['profile'], 96000)
                as_audio.addRepresentation(audio_representation)
                period.addAdaptationSetAudio(as_audio)
            video_representation = MPDRepresentation.Video('video-%s' % p['profile'], p['stream'].bandwidth, p['stream'].resolution[0], p['stream'].resolution[1])
            period.getAdaptationSetVideo().addRepresentation(video_representation)
        
    def _parseMaster(self, variant):
        debug.log("Parsing master playlist")
        for playlist in variant.playlists:
            stream = playlist.stream_info
            (video_codec, audio_codec) = stream.codecs.split(',')
            profile = self._profileFromFilename(playlist.uri) 
            profilemetadata = {
                'profile': profile,
                'videocodec': video_codec,
                'audiocodec': audio_codec,
                'stream': stream
            }
            self.profiles.append(profilemetadata)
        self._initiatePeriod(self.getPeriod(self.currentPeriodIdx), self.profiles)


