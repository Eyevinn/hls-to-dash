# Description

This is an open source video streaming packager and toolkit to rewrap live HLS streams to live MPEG DASH streams. 

## Features
 - Generate single period MPEG DASH for live based on an HLS live stream
 - Generate multi period MPEG DASH for live based on an HLS live stream with SCTE35 splicing

# Usage

## Install

Installation from source:

     python setup.py install

## Running

Generate Single period MPEG DASH:

     hls-to-dash http://example.com/master.m3u8 > stream.mpd

Generate Multi period MPEG DASH:

     hls-to-dash http://example.com/master.m3u8 --multi > stream.mpd

## Help

```
usage: hls-to-dash [-h] [--multi] [--ctx CTX] [--ctxdir CTXDIR] [--debug]
                   PLAYLIST

Generate single and multi period MPEG DASH manifest from a live HLS source.
Writes MPEG DASH manifest to stdout.

Currently assumes that HLS variant is named as 'master[PROFILE].m3u8'
  master2500.m3u8, master1500.m3u8
and that the segments are named as 'master[PROFILE]_[SEGNO].ts'
  master2500_34202.ts, master1500_34202.ts

positional arguments:
  PLAYLIST         Path to HLS playlist file. Can be a URI or local file.

optional arguments:
  -h, --help       show this help message and exit
  --multi          Generate multi period MPEG DASH on EXT-X-CUE markers in HLS
  --ctx CTX        Name of DASH session file
  --ctxdir CTXDIR  Where to store DASH session file. Defaults to /tmp/
  --debug          Write debug info to stderr
```

