import pycurl
from ffprobe import FFProbe
import tempfile

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


class Remote(Base):
    def __init__(self, uri):
        Base.__init__(self)
        self.uri = uri
    def probe(self):
        tmpfile = tempfile.NamedTemporaryFile()
        c = pycurl.Curl()
        c.setopt(c.URL, self.uri)
        c.setopt(c.WRITEDATA, tmpfile)
        c.perform()
        c.close
        self.parsedata(FFProbe(tmpfile.name))
        tmpfile.close()

class Local(Base):
    def __init__(self, path):
        Base.__init__(self)
        self.path = path
    def probe(self):
        self.parsedata(FFProbe(self.path))

class Stream:
    def __init__(self, streamid):
        self.id = streamid


