# Copyright 2016 Eyevinn Technology. All rights reserved
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.
# Author: Jonas Birme (Eyevinn Technology)

import argparse
import pkg_resources
from hls2dash.lib import MPD
from hls2dash import debug

def VERSION():
    version = pkg_resources.require('hls2dash')[0].version
    return version

def main():
    version = VERSION()
    parser = argparse.ArgumentParser(
        description="Generate single and multi period MPEG DASH manifest from a live HLS source.\n" 
                    "Writes MPEG DASH manifest to stdout.\n\n"
                    "Currently assumes that HLS variant is named as 'master[PROFILE].m3u8'\n" 
                    "  master2500.m3u8, master1500.m3u8\n"
                    "and that the segments are named as 'master[PROFILE]_[SEGNO].ts'\n"
                    "  master2500_34202.ts, master1500_34202.ts\n" 
        ,formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('playlist', metavar='PLAYLIST', help='Path to HLS playlist file. Can be a URI or local file.')
    parser.add_argument('--multi', dest='multi', action='store_true', default=False, help='Generate multi period MPEG DASH on EXT-X-CUE markers in HLS')
    parser.add_argument('--ctx', dest='ctx', default=None, help='Name of DASH session file')
    parser.add_argument('--ctxdir', dest='ctxdir', default='/tmp/', help='Where to store DASH session file. Defaults to /tmp/')
    parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='Write debug info to stderr')
    parser.add_argument('--version', action='version', version='%(prog)s ('+version+')')
    args = parser.parse_args()
    debug.doDebug = args.debug

    mpd = MPD.HLS(args.playlist, args.multi, args.ctxdir, args.ctx)
    mpd.setVersion(VERSION())
    mpd.load()
    print(mpd.asXML())

if __name__ == '__main__':
    try: 
        main()
    except Exception, err:
        raise

