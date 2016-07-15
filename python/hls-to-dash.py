# Depends on patched mp4packager (Bento4)
# Author: Jonas Birme (Eyevinn Technology)

import argparse
from lib import MPD
import debug

def main():
    parser = argparse.ArgumentParser(description='Generate an MPEG DASH manifest from a live HLS source including the option to download and rewrap TS segments to MP4 fragments. Writes MPEG DASH manifest to stdout')
    parser.add_argument('playlist', metavar='PLAYLIST', help='Path to HLS playlist file. Can be a URI or local file.')
    parser.add_argument('--multi', dest='multi', action='store_true', default=False, help='Generate multi period MPEG DASH on EXT-X-CUE markers in HLS')
    parser.add_argument('--remux', dest='remux', action='store_true', default=False, help='download and remux TS segments to MP4 fragments (requires ffmpeg and patched mp4packager (Bento4)')
    parser.add_argument('--renumber', dest='renumber', action='store_true', default=False, help='Renumber all segments. Can only be used in combination with --remux')
    parser.add_argument('--debug', dest='debug', action='store_true', default=False)
    args = parser.parse_args()
    debug.doDebug = args.debug

    mpd = MPD.HLS(args.playlist)
    mpd.load()
    print(mpd.asXML())

if __name__ == '__main__':
    try: 
        main()
    except Exception, err:
        raise

