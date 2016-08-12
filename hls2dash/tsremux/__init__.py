# Copyright 2016 Eyevinn Technology. All rights reserved
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.
# Author: Jonas Birme (Eyevinn Technology)

import argparse
from hls2dash import debug

def main():
    parser = argparse.ArgumentParser(
        description="Rewrap a MPEG2 TS segment to a fragmented MP4"
        ,formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('tsfile', metavar='TSFILE', help='Path to TS file. Can be a URI or local file.')
    parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='Write debug info to stderr')
    args = parser.parse_args()
    debug.doDebug = args.debug

    ts = None
    if re.match('^http', args.tsfile):
        ts = TS.Remote(args.tsfile)
    else:
        ts = TS.Local(args.tsfile)

