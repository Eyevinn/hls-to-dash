# Copyright 2016 Eyevinn Technology. All rights reserved
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.
# Author: Jonas Birme (Eyevinn Technology)

import argparse
import pkg_resources
import re
from hls2dash import debug
from hls2dash.lib import TS

def main():
    version = pkg_resources.require('hls2dash')[0].version
    parser = argparse.ArgumentParser(
        description="Rewrap a MPEG2 TS segment to a fragmented MP4"
        ,formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('tsfile', metavar='TSFILE', help='Path to TS file. Can be a URI or local file.')
    parser.add_argument('output', metavar='OUTPUT', help='Output file name')
    parser.add_argument('--outdir', dest='outdir', default='.', help='Directory where the fragmented MP4 will be stored. Default is current directory')
    parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='Write debug info to stderr')
    parser.add_argument('--version', action='version', version='%(prog)s ('+version+')')
    args = parser.parse_args()
    debug.doDebug = args.debug

    ts = None
    if re.match('^http', args.tsfile):
        ts = TS.Remote(args.tsfile)
    else:
        ts = TS.Local(args.tsfile)
    ts.remuxMP4(args.outdir, args.output)
