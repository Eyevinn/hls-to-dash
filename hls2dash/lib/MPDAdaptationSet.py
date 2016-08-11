# Copyright 2016 Eyevinn Technology. All rights reserved
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.
# Author: Jonas Birme (Eyevinn Technology)

class Base:
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
        self.presentationTimeOffset = int(float(startTime) * self.timescale)
    def __str__(self):
        s = "(mimeType=%s, codec=%s, representations=%d):\n" % (self.mimeType, self.codec, len(self.representations))
        for r in self.representations:
            s += "        + " + str(r) + "\n"
        for seg in self.segments:
            s += "           + " + str(seg) + "\n"
        return s

class Video(Base):
    def __init__(self, mimeType, codec):
        Base.__init__(self, mimeType, codec, 90000)
    def asXML(self):
        idxlist = xrange(len(self.representations))
        maxWidth = self.representations[max(idxlist, key = lambda x: self.representations[x].getWidth())].getWidth()
        maxHeight = self.representations[max(idxlist, key = lambda x: self.representations[x].getHeight())].getHeight()
        maxBandwidth = self.representations[max(idxlist, key = lambda x: self.representations[x].getBandwidth())].getBandwidth()
        minWidth = self.representations[min(idxlist, key = lambda x: self.representations[x].getWidth())].getWidth()
        minHeight = self.representations[min(idxlist, key = lambda x: self.representations[x].getHeight())].getHeight()
        minBandwidth = self.representations[min(idxlist, key = lambda x: self.representations[x].getBandwidth())].getBandwidth()
        xml = ''
        xml += '    <AdaptationSet mimeType="%s" codecs="%s" minWidth="%d" maxWidth="%d" minHeight="%d" maxHeight="%d" startWithSAP="1" segmentAlignment="true" minBandwidth="%d" maxBandwidth="%d">\n' % (self.mimeType, self.codec, minWidth, maxWidth, minHeight, maxHeight, minBandwidth, maxBandwidth)
        xml += '      <SegmentTemplate timescale="%d" media="$RepresentationID$_$Number$.dash" presentationTimeOffset="%s" startNumber="%s">\n' % (self.timescale, self.presentationTimeOffset, self.startNumber)
        xml += '        <SegmentTimeline>\n';
        for s in self.segments:
            xml += s.asXML()
        xml += '        </SegmentTimeline>\n';
        xml += '      </SegmentTemplate>\n'
        for r in self.representations:
            xml += r.asXML()
        xml += '    </AdaptationSet>\n'
        return xml

class Audio(Base):
    def __init__(self, mimeType, codec):
        Base.__init__(self, mimeType, codec, 48000)
    def asXML(self):
        xml = ''
        xml += '    <AdaptationSet mimeType="%s" codecs="%s">\n' % (self.mimeType, self.codec)
        xml += '      <SegmentTemplate timescale="%d" media="$RepresentationID$_$Number$.dash" presentationTimeOffset="%s" startNumber="%s">\n' % (self.timescale, self.presentationTimeOffset, self.startNumber)
        xml += '        <SegmentTimeline>\n';
        for s in self.segments:
            xml += s.asXML()
        xml += '        </SegmentTimeline>\n';
        xml += '      </SegmentTemplate>\n'
        for r in self.representations:
            xml += r.asXML()
        xml += '    </AdaptationSet>\n'
        return xml


