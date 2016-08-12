# Copyright 2016 Eyevinn Technology. All rights reserved
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.
# Author: Jonas Birme (Eyevinn Technology)


import pycurl
from ffprobe import FFProbe
import tempfile
import re
import os
from hls2dash.lib.TSRemux import tsremux
from hls2dash import debug

class Base:
    def __init__(self):
        self.startTime = 0
        self.duration = 0
        self.streams = []
    def parsedata(self, probedata):
        if len(probedata.streams) > 0:
            self.startTime = float(probedata.streams[0].start_time)
    def getStartTime(self):
        return self.startTime
    def cleanup(self):
        return


class Remote(Base):
    def __init__(self, uri):
        Base.__init__(self)
        self.uri = uri
        self.downloadedFile = None
        self.tmpdir = '/tmp/'
        self._initTempFile()
    def setTmpDir(self, tmpdir):
        self.tmpdir = tmpdir
        if not self.tmpdir.endswith('/'):
            self.tmpdir += '/'
        self._initTempFile()
    def _initTempFile(self):
        res = re.match('.*/(.*\.ts)$', self.uri)
        self.fname = res.group(1)
        self.fpath = self.tmpdir + self.fname
    def download(self):
        if self.downloadedFile == None:
            debug.log("Downloading %s to %s" % (self.uri, self.fname))
            self.downloadedFile = open(self.fpath, 'wb')
            c = pycurl.Curl()
            c.setopt(c.URL, self.uri)
            c.setopt(c.WRITEDATA, self.downloadedFile)
            c.perform()
            c.close
            self.downloadedFile.close()
    def probe(self):
        self.download()
        self.parsedata(FFProbe(self.downloadedFile.name))
    def remuxMP4(self, outdir, filename):
        self.download()
        self.probe()
        tsremux(self.downloadedFile.name, outdir, filename, self.getStartTime())
        self.cleanup()
    def getFilename(self):
        return self.downloadedFile.name
    def cleanup(self):
        os.remove(self.fpath)

class Local(Base):
    def __init__(self, path):
        Base.__init__(self)
        self.path = path
    def probe(self):
        self.parsedata(FFProbe(self.path))
    def remuxMP4(self, outdir, filename):
        self.probe()
        tsremux(self.path, outdir, filename, self.getStartTime())
    def getFilename(self):
        return self.path

class Stream:
    def __init__(self, streamid):
        self.id = streamid


