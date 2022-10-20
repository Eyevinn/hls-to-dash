# Copyright 2016 Eyevinn Technology. All rights reserved
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.
# Author: Jonas Birme (Eyevinn Technology)

import tempfile
import re
import m3u8
import time
import datetime
import pycurl
import os
import json
from ffprobe import FFProbe
from hls2dash.lib import util
from hls2dash.lib import MPDAdaptationSet
from hls2dash.lib import MPDRepresentation
from hls2dash.lib import TS
from hls2dash import debug
import sys

# Represents an MPEG DASH period
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
        event = SCTE35Event(id, util.NUM(duration), scte35)
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

# An MPEG DASH Event (base class)
class PeriodEvent:
    def __init__(self, id, duration):
        self.duration = duration
        self.id = id
        self.timescale = 90000
    def getTimescale(self):
        return self.timescale
    def getId(self):
        return self.id

# SCTE35 as an MPEG DASH Event
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

# Store context state between executions
class Context:
    def __init__(self, name, dir='/tmp/'):
        if not dir.endswith('/'):
            dir += '/'
        self.filename = dir + name + '.ctx'
        #self.filename = '/tmp/' + 'TEST' + '.ctx'
        self.timebase = 90000.0
        self.prevSplitTS = None
        self.nextSplitTS = None
    def getPrevSplit(self):
        if self.prevSplitTS == None:
            return 0
        return self.prevSplitTS
    def setPrevSplit(self, t):
        self.prevSplitTS = int(float(t) * self.timebase)
    def getNextSplit(self):
        if self.nextSplitTS == None:
            return 0
        return self.nextSplitTS
    def setNextSplit(self, t):
        self.nextSplitTS = int(float(t) * self.timebase)
    def getTimeBase(self):
        return float(self.timebase)
    def resetNextSplit(self):
        self.nextSplitTS = None
    def restore(self):
        debug.log('Restoring context from %s' % self.filename)
        if os.path.isfile(self.filename):
            with open(self.filename, 'r+') as f:
                data = f.read()
                obj = json.loads(data)
                self.timebase = obj['timebase']
                if 'prevsplit' in obj:
                    self.prevSplitTS = obj['prevsplit']
                if 'nextsplit' in obj:
                    self.nextSplitTS = obj['nextsplit']
        debug.log('Context: %s' % self)
    def save(self):
        obj = {}
        obj['timebase'] = self.timebase
        if self.prevSplitTS != None:
            obj['prevsplit'] = self.prevSplitTS
        if self.nextSplitTS != None:
            obj['nextsplit'] = self.nextSplitTS
        with open(self.filename, 'w+') as f:
            f.seek(0)
            f.write(json.dumps(obj, indent=4))
            f.truncate()
        debug.log('Saved context %s to %s' % (obj, self.filename))
    def __str__(self):
        s = 'timebase=%d' % self.timebase
        if self.prevSplitTS != None:
            s += ',prevsplit=%d' % self.prevSplitTS
        if self.nextSplitTS != None:
            s += ',nextsplit=%d' % self.nextSplitTS
        return s

# MPEG DASH manifest (base class)
class Base:
    def __init__(self):
        self.maxSegmentDuration = 10
        self.firstSegmentStartTime = 0
        self.periods = []
        period = Period('1')
        period.setPeriodStart(0.0)
        self.appendPeriod(period)
        self.version = 'UNDEF'
    def setVersion(self, version):
        self.version = version
    def havePeriods(self):
        return len(self.periods) > 0
    def getPeriod(self, idx):
        return self.periods[idx]
    def getAllPeriods(self):
        return self.periods;
    def appendPeriod(self, period):
        self.periods.append(period)
    def asXML(self):
        xml = '<?xml version="1.0"?>\n';
        xml += '<!-- Created with hls2dash (version=%s) -->\n' % self.version;
        xml += '<!-- https://pypi.python.org/pypi/hls2dash -->\n'
        xml += '<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" xmlns:scte35="urn:scte:scte35:2014:xml+bin" profiles="urn:mpeg:dash:profile:isoff-live:2011" type="dynamic" minimumUpdatePeriod="PT10S" minBufferTime="PT1.500S" maxSegmentDuration="%s" availabilityStartTime="%s" publishTime="%s">\n' % (util.PT(self.maxSegmentDuration), self._getAvailabilityStartTime(), self._getPublishTime())
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
 
# MPEG DASH manifest from a HLS manifest
class HLS(Base):
    def __init__(self, playlistlocator, splice=False, ctxdir='/tmp/', ctxname=None):
        Base.__init__(self)
        self.playlistlocator = playlistlocator
        self.profilepattern = '^\D+(\d+.*)\.m3u8$'
        self.numberpattern = '^.+\D+(\d+)\.ts$'
        self.isRemote = False
        self.baseurl = ''
        res = re.match('^(.*)/.*.m3u8$', playlistlocator)
        if res:
            self.baseurl = res.group(1) + '/'
	if re.match('^http', playlistlocator):
            self.isRemote = True
        self.currentPeriodIdx = 0
        self.profiles = []

        # If enabled splice into multi periods on SCTE35 markers
        self.splitperiod = splice

        # By default use directory name as name for this stream
        if ctxname == None:
            r = re.match('^.*/(.*?)/.*.m3u8$', playlistlocator)
            if r:
                self.name = r.group(1)
            if self.splitperiod == True:
                self.name += '_multi'
        else:
            self.name = ctxname
        if self.name == None:
            raise Exception("Invalid playlistlocator, not an m3u8 file")
        self.context = Context(self.name, ctxdir)

    def setProfilePattern(self, profilepattern):
        self.profilepattern = profilepatten

    def load(self):
        self.context.restore()
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
        self.context.save()

    def _profileFromFilename(self, filename):
        result = re.match(self.profilepattern, filename)
        if result:
            debug.log("Profile=%s (filename=%s, pattern=%s)" %
                      (result.group(1), filename, self.profilepattern))
            return result.group(1)
        else:
            exit("Error: Can't extract profile from filename=%s (pattern=%s)" %
                 (filename, self.profilepattern))

    def _getStartNumberFromFilename(self, filename):
        result = re.match(self.numberpattern, filename)
        if result:
            debug.log("StartNumber=%s (filename=%s, pattern=%s)" %
                      (result.group(1), filename, self.numberpattern))
            return result.group(1)
        debug.log("Warning: Can't extract start number from filename %s, using 0 (pattern=%s)" %
                  (filename, self.numberpattern))
        return '0'

    def _parsePlaylist(self, playlist):
        debug.log("Splicing enabled=%s" % self.splitperiod)
        self.maxSegmentDuration = playlist.target_duration
        isFirstInPeriod = True
        isFirst = True
        doSplit = False
        eventid = 1
        offset = 0.0
        state = 'initial'
        isFirstSplit = True
        lastnumber = None
        periodid = 'UNDEF'
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
            #debug.log("[%s][P%d]: %s" % (state, self.currentPeriodIdx, seg.uri))

            if self.splitperiod and doSplit:
                debug.log("-- Split period before %s" % seg.uri)
                self.currentPeriodIdx = self.currentPeriodIdx + 1
                newperiod = Period("P%s" % self._getStartNumberFromFilename(seg.uri))
                self._initiatePeriod(newperiod, self.profiles)
                self.appendPeriod(newperiod)
                isFirstInPeriod = True
                doSplit = False
            duration = float(seg.duration)
            videoseg = MPDRepresentation.Segment(duration, isFirstInPeriod)
            audioseg = MPDRepresentation.Segment(duration, isFirstInPeriod)
            period = self.getPeriod(self.currentPeriodIdx)
            period.getAdaptationSetVideo().addSegment(videoseg)
            period.getAdaptationSetAudio().addSegment(audioseg)
            period.increaseDuration(duration)
            offset += duration
            if isFirstInPeriod:
                # Add EventStream to place SCTE35 metadata
                debug.log("SCTE35:%s (%s, %s)" % (seg.scte35, seg.cue_out, state))
                if state == 'insidecue' and seg.cue_out == True:
                    period.addSCTE35Splice(eventid, seg.scte35_duration, seg.scte35)
                    eventid = eventid + 1
                # Obtain the start time for the first segment in this period
                firstStartTimeInPeriod = self._getStartTimeFromFile(seg.base_uri + seg.uri)
                firstStartTimeInPeriodTicks = int(float(firstStartTimeInPeriod) * self.context.getTimeBase())
                # Determine the period ID
                if isFirst == True:
                    debug.log('firstStartTimeInPeriod=%d, prevsplit=%d' % (firstStartTimeInPeriodTicks, self.context.getPrevSplit()))
                    # Store the first segment start time in this manifest
                    # to be able to calculate the MPD availability start time
                    self.firstSegmentStartTime = firstStartTimeInPeriod
                    # As this is the very first period and we then need to determine
                    # whether the first segment belongs to a period created
                    # in previous manifest so the correct period id is set
                    if self.context.getPrevSplit() == 0:
                        # We have no information of previous split so use
                        # the start time in this period as period id
                        # and save it for later use
                        self.context.setPrevSplit(firstStartTimeInPeriod)
                        periodid = self.context.getPrevSplit()
                    elif firstStartTimeInPeriodTicks < 0:
                        # Start time for a segment can actually be negative. No
                        # good way to handle it but as long as it is increasing
                        # it will eventually be back to normal
                        periodid = firstStartTimeInPeriodTicks
                        self.context.setPrevSplit(firstStartTimeInPeriod)
                    elif firstStartTimeInPeriodTicks >= self.context.getPrevSplit():
                        if self.context.getNextSplit() == 0:
                            periodid = self.context.getPrevSplit()
                        elif firstStartTimeInPeriodTicks < self.context.getNextSplit():
                            # Start time for the first segment in this period
                            # is still before the next split and we should use
                            # period id belonging to previous manifest
                            periodid = self.context.getPrevSplit()
                        else:
                            # Start time for the first segment in this period
                            # belongs to a new period unless this is the only period
                            # in this manifest and is actually the last split
                            if self.context.getNextSplit() < self.context.getPrevSplit():
                                period = self.context.getPrevSplit()
                            else:
                                periodid = firstStartTimeInPeriodTicks
                                self.context.setPrevSplit(firstStartTimeInPeriod)
                    elif firstStartTimeInPeriodTicks < self.context.getPrevSplit():
                        # If start time of first segment is smaller than ts of
                        # last split a segment time stamp reset / overflow must have
                        # occured
                        periodid = firstStartTimeInPeriodTicks
                        self.context.setPrevSplit(firstStartTimeInPeriod)
                else:
                    # Start time for the first segment in this period after a split
                    # is the period id
                    periodid = firstStartTimeInPeriodTicks
                    if isFirstSplit == True:
                        # Save the segment start time for the first split
                        self.context.setNextSplit(firstStartTimeInPeriod)
                        isFirstSplit = False
                period.setPeriodId(periodid)
                # Set period start time
                periodstartsec = float(periodid / self.context.getTimeBase())
                period.setPeriodStart(periodstartsec)
                # Set segment start time and start number for the video and audio segments
                videoseg.setStartTime(firstStartTimeInPeriod)
                audioseg.setStartTime(firstStartTimeInPeriod)
                as_audio = period.getAdaptationSetAudio()
                as_video = period.getAdaptationSetVideo()
                as_video.setStartNumber(self._getStartNumberFromFilename(seg.uri))
                as_video.setStartTime(periodstartsec)
                as_audio.setStartNumber(self._getStartNumberFromFilename(seg.uri))
                as_audio.setStartTime(periodstartsec)
            isFirstInPeriod = False
            isFirst = False
        if self.context.getNextSplit() < self.context.getPrevSplit():
            # No new split in this manifest, last split is the current one
            self.context.resetNextSplit()
        allperiods = self.getAllPeriods()
        lastperiod = allperiods[len(allperiods)-1]
        lastperiod.setAsLastPeriod()
    
    def _getStartTimeFromFile(self, uri):
        if self.isRemote:
            if not re.match('^http', uri):
                uri = self.baseurl + uri
            ts = TS.Remote(uri)
        else:
            ts = TS.Local(uri)
        ts.probe()
        ts.cleanup()
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
            if stream.codecs:
                (video_codec, audio_codec) = stream.codecs.split(',')
            else:
                debug.log("Warning: No codecs defined")
                audio_codec = ''
                video_codec = ''
            profile = self._profileFromFilename(playlist.uri) 
            profilemetadata = {
                'profile': profile,
                'videocodec': video_codec,
                'audiocodec': audio_codec,
                'stream': stream
            }
            self.profiles.append(profilemetadata)
        self._initiatePeriod(self.getPeriod(self.currentPeriodIdx), self.profiles)


