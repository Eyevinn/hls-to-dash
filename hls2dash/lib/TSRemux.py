# Copyright 2016 Eyevinn Technology. All rights reserved
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.
# Author: Jonas Birme (Eyevinn Technology)

import tempfile
import shlex
import os
import subprocess
from hls2dash import debug

def tsremux(tsfile, outdir, filename, starttime):
    audiofile = '%s/audio-%s' % (outdir, filename)
    videofile = '%s/video-%s' % (outdir, filename)
    debug.log("Remuxing %s to %s and %s" % (tsfile, audiofile, videofile))
    tmpaudio = tempfile.NamedTemporaryFile(dir='/tmp/', suffix='.mp4')
    tmpvideo = tempfile.NamedTemporaryFile(dir='/tmp/', suffix='.mp4')
    FFMpegCommand(tsfile, tmpaudio.name, '-y -bsf:a aac_adtstoasc -acodec copy -vn')
    FFMpegCommand(tsfile, tmpvideo.name, '-y -vcodec copy -an')
    Mp4Fragment(tmpaudio.name, audiofile, starttime)
    Mp4Fragment(tmpvideo.name, videofile, starttime)

def runcmd(cmd, name):
    debug.log('COMMAND: %s' % cmd)
    try:
        FNULL = open(os.devnull, 'w')
        if debug.doDebug:
            return subprocess.call(cmd)
        else:
            return subprocess.call(cmd, stdout=FNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        message = "binary tool failed with error %d" % e.returncode
        raise Exception(message)
    except OSError as e:
        raise Exception('Command %s not found, ensure that it is in your path' % name)

def FFMpegCommand(infile, outfile, opts):
    cmd = [os.path.basename('ffmpeg')]
    cmd.append('-i')
    cmd.append(infile)
    args = shlex.split(opts)
    cmd += args
    cmd.append(outfile)
    runcmd(cmd, 'ffmpeg')

def Mp4Fragment(infile, outfile, starttime):
    cmd = [os.path.basename('mp4fragment')]
    opts = '--tfdt-start %f' % starttime
    args = shlex.split(opts)
    cmd += args
    cmd.append(infile)
    cmd.append(outfile)
    runcmd(cmd, 'mp4fragment')

