# Copyright 2016 Eyevinn Technology. All rights reserved
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.
# Author: Jonas Birme (Eyevinn Technology)

from hls2dash import debug

def TSRemux(tsfile, outdir, profile, starttime):
    debug.log("Remuxing %s to fMP4" % tsfile)
