#!/usr/bin/env python
# Depends on patched mp4packager (Bento4)
# Author: Jonas Birme (Eyevinn Technology)

from __future__ import print_function
import m3u8
import argparse
import sys
import pycurl
import re
import tempfile
from ffprobe import FFProbe

class PT:
    def __init__(self, seconds):
        self.seconds = seconds
    def __str__(self):
        return "PT%dS" % self.seconds

class MPD_Segment:
    def __init__(self, duration, isFirst):
        self.duration = duration
        self.timescale = 1
        self.startTime = 0
        self.isFirst = isFirst
    def setTimescale(self, timescale):
        self.timescale = timescale 
    def setStartTime(self, startTime):
        self.startTime = startTime
    def asXML(self):
        if self.isFirst:
            xml = '        <S t="%d" d="%d" />\n' % (self.startTime * self.timescale, self.duration * self.timescale)
        else:
            xml = '        <S d="%d" />\n' % (self.duration * self.timescale)
        return xml
    def __str__(self):
        return '(duration=%s)' % (self.duration)

class MPD_Representation:
    def __init__(self, representationid, bandwidth):
        self.id = representationid
        self.bandwidth = bandwidth
    def getBandwidth(self):
        return self.bandwidth
    def asXML(self):
        xml = '      <Representation id="%s" bandwidth="%s" />\n' % (self.id, self.bandwidth)
        return xml
    def __str__(self):
        return "(id=%s, bandwidth=%s)" % (self.id, self.bandwidth)

class MPD_RepresentationVideo(MPD_Representation):
    def __init__(self, representationid, bandwidth, width, height):
        MPD_Representation.__init__(self, representationid, bandwidth)
        self.width = width
        self.height = height
    def getHeight(self):
        return self.height
    def getWidth(self):
        return self.width
    def asXML(self):
        xml = '      <Representation id="%s" width="%s" height="%s" bandwidth="%s" scanType="progressive" />\n' % (self.id, self.width, self.height, self.bandwidth)
        return xml
    def __str__(self):
        return "(id=%s, bandwidth=%s, width=%s, height=%s)" % (self.id, self.bandwidth, self.width, self.height)


class MPD_AdaptationSet:
    def __init__(self, mimeType, codec, timescale):
        self.representations = []
        self.segments = []
        self.mimeType = mimeType
        self.codec = codec
        self.timescale = timescale
        self.startNumber = '0'
        self.presentationTimeOffset = 0
    def addRepresentation(self, representation):
        self.representations.append(representation)
    def addSegment(self, segment):
        segment.setTimescale(self.timescale)
        self.segments.append(segment)
    def setStartNumber(self, startNumber):
        self.startNumber = startNumber.lstrip('0')
    def setStartTime(self, startTime):
        self.presentationTimeOffset = startTime * self.timescale
    def __str__(self):
        s = "(mimeType=%s, codec=%s, representations=%d):\n" % (self.mimeType, self.codec, len(self.representations))
        for r in self.representations:
            s += "        + " + str(r) + "\n"
        return s

class MPD_AdaptationSetVideo(MPD_AdaptationSet):
    def __init__(self, mimeType, codec):
        MPD_AdaptationSet.__init__(self, mimeType, codec, 90000)
    def asXML(self):
        idxlist = xrange(len(self.representations))
        maxWidth = self.representations[max(idxlist, key = lambda x: self.representations[x].getWidth())].getWidth()
        maxHeight = self.representations[max(idxlist, key = lambda x: self.representations[x].getHeight())].getHeight()
        maxBandwidth = self.representations[max(idxlist, key = lambda x: self.representations[x].getBandwidth())].getBandwidth()
        minWidth = self.representations[min(idxlist, key = lambda x: self.representations[x].getWidth())].getWidth()
        minHeight = self.representations[min(idxlist, key = lambda x: self.representations[x].getHeight())].getHeight()
        minBandwidth = self.representations[min(idxlist, key = lambda x: self.representations[x].getBandwidth())].getBandwidth()
        xml = ''
        xml += '    <AdaptationSet mimeType="%s" codecs="%s" segmentAlignment="true" minWidth="%d" maxWidth="%d" minHeight="%d" maxHeight="%d" startWithSAP="1" minBandwidth="%d" maxBandwidth="%d">\n' % (self.mimeType, self.codec, minWidth, minHeight, maxWidth, maxHeight, minBandwidth, maxBandwidth)
        xml += '      <SegmentTemplate timescale="%d" media="$RepresentationID$_$Number$.dash" startNumber="%s" presentationTimeOffset="%d">\n' % (self.timescale, self.startNumber, self.presentationTimeOffset)
        xml += '        <SegmentTimeline>\n';
        for s in self.segments:
            xml += s.asXML()
        xml += '        </SegmentTimeline>\n';
        xml += '      </SegmentTemplate>\n'
        for r in self.representations:
            xml += r.asXML()
        xml += '    </AdaptationSet>\n'
        return xml

class MPD_AdaptationSetAudio(MPD_AdaptationSet):
    def __init__(self, mimeType, codec):
        MPD_AdaptationSet.__init__(self, mimeType, codec, 48000)
    def asXML(self):
        xml = ''
        xml += '    <AdaptationSet mimeType="%s" codecs="%s">\n' % (self.mimeType, self.codec)
        xml += '      <SegmentTemplate timescale="%d" media="$RepresentationID$_$Number$.dash" startNumber="%s" presentationTimeOffset="%d">\n' % (self.timescale, self.startNumber, self.presentationTimeOffset)
        xml += '        <SegmentTimeline>\n';
        for s in self.segments:
            xml += s.asXML()
        xml += '        </SegmentTimeline>\n';
        xml += '      </SegmentTemplate>\n'
        for r in self.representations:
            xml += r.asXML()
        xml += '    </AdaptationSet>\n'
        return xml

class MPD:
    def __init__(self, playlistlocator):
        self.playlistlocator = playlistlocator
        self.as_video = None
        self.as_audio = None
        self.profilepattern = 'master(\d+).m3u8'
        self.numberpattern = 'master\d+_(\d+).ts'
        self.maxSegmentDuration = 10
        self.periodDuration = 30
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
        debug_print("Loading playlist: ", self.playlistlocator)
        m3u8_obj = m3u8.load(self.playlistlocator)
        if m3u8_obj.is_variant:
            if m3u8_obj.playlist_type == "VOD":
                raise Exception("VOD playlists not yet supported")
            self._parseMaster(m3u8_obj)
        else:
            raise Exception("Can only create DASH manifest from an HLS master playlist")
        if Options.remux:
            debug_print("Remuxing segments")
        p = m3u8_obj.playlists[0]
        debug_print("Loading playlist: ", self.baseurl + p.uri)
        self._parsePlaylist(m3u8.load(self.baseurl + p.uri))
        #debug_print("Audio: ", self.as_audio)
        #debug_print("Video: ", self.as_video)

    def asXML(self):
        xml = '<?xml version="1.0"?>';
        xml += '<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" profiles="urn:mpeg:dash:profile:isoff-live:2011" type="dynamic" minimumUpdatePeriod="PT20S" minBufferTime="PT1.500S" maxSegmentDuration="%s">\n' % (PT(self.maxSegmentDuration))
        xml += '  <Period id="1" start="PT0S" duration="%s">\n' % PT(self.periodDuration)
        xml += self.as_video.asXML()
        xml += self.as_audio.asXML()
        xml += '  </Period>\n'
        xml += '</MPD>\n'
        return xml

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
            duration = int(seg.duration)
            videoseg = MPD_Segment(duration, isFirst)
            audioseg = MPD_Segment(duration, isFirst)
            self.as_video.addSegment(videoseg)
            self.as_audio.addSegment(audioseg)
            self.periodDuration += duration
            if isFirst:
                startTime = self._getStartTimeFromFile(seg.uri)
                videoseg.setStartTime(startTime)
                audioseg.setStartTime(startTime)
                self.as_video.setStartNumber(self._getStartNumberFromFilename(seg.uri))
                self.as_video.setStartTime(startTime)
                self.as_audio.setStartNumber(self._getStartNumberFromFilename(seg.uri))
                self.as_audio.setStartTime(startTime)
            isFirst = False
    
    def _getStartTimeFromFile(self, uri):
        if self.isRemote:
            tmpfile = tempfile.NamedTemporaryFile()
            if not re.match('^http', uri):
                uri = self.baseurl + uri
            c = pycurl.Curl()
            c.setopt(c.URL, uri)
            c.setopt(c.WRITEDATA, tmpfile)
            c.perform()
            c.close()
            probedata = FFProbe(tmpfile.name)
            tmpfile.close()
        else:
            probedata = FFProbe(self.baseurl + uri)
        if len(probedata.streams) > 0:
           return int(float(probedata.streams[0].start_time))
        
    def _parseMaster(self, variant):
        debug_print("Parsing master playlist")
        for playlist in variant.playlists:
            stream = playlist.stream_info
            (video_codec, audio_codec) = stream.codecs.split(',')
            profile = self._profileFromFilename(playlist.uri) 
            if self.as_video == None:
                self.as_video = MPD_AdaptationSetVideo('video/mp4', video_codec)
            if self.as_audio == None:
                self.as_audio = MPD_AdaptationSetAudio('audio/mp4', audio_codec)
                audio_representation = MPD_Representation('audio-%s' % profile, 96000)
                self.as_audio.addRepresentation(audio_representation)
            video_representation = MPD_RepresentationVideo('video-%s' % profile, stream.bandwidth, stream.resolution[0], stream.resolution[1])
            self.as_video.addRepresentation(video_representation)

def debug_print(*args, **kwargs):
    if Options.debug:
        print(*args, file=sys.stderr, **kwargs)

Options = None
def main():
    parser = argparse.ArgumentParser(description='Generate an MPEG DASH manifest from a live HLS source including the option to download and rewrap TS segments to MP4 fragments. Writes MPEG DASH manifest to stdout')
    parser.add_argument('playlist', metavar='PLAYLIST', help='Path to HLS playlist file. Can be a URI or local file.')
    parser.add_argument('--remux', dest='remux', action='store_true', default=False, help='download and remux TS segments to MP4 fragments (requires ffmpeg and patched mp4packager (Bento4)')
    parser.add_argument('--debug', dest='debug', action='store_true', default=False)
    args = parser.parse_args()
    global Options
    Options = args

    mpd = MPD(args.playlist)
    mpd.load()
    print(mpd.asXML())

if __name__ == '__main__':
    try: 
        main()
    except Exception, err:
        raise

