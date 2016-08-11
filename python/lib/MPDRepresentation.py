# Copyright 2016 Eyevinn Technology. All rights reserved
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.
# Author: Jonas Birme (Eyevinn Technology)


class Segment:
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
            xml = '          <S t="%d" d="%d" />\n' % (int(self.startTime * self.timescale), self.duration * self.timescale)
        else:
            xml = '          <S d="%d" />\n' % (int(self.duration * self.timescale))
        return xml
    def __str__(self):
        return '(duration=%s)' % (self.duration)

class Base:
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

class Video(Base):
    def __init__(self, representationid, bandwidth, width, height):
        Base.__init__(self, representationid, bandwidth)
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

class Audio(Base):
    def __init__(self, representationid, bandwidth):
        Base.__init__(self, representationid, bandwidth)
     

