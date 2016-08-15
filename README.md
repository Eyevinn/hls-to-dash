![Build status](https://travis-ci.org/Eyevinn/hls-to-dash.svg?branch=master)

# Description

This is an open source video streaming packager and toolkit to rewrap live HLS streams to live MPEG DASH streams. 

## Features
 - Generate single period MPEG DASH for live based on an HLS live stream
 - Generate multi period MPEG DASH for live based on an HLS live stream with SCTE35 splicing
 - Rewrap MPEG2 TS segment to fragmented MP4

# Usage

## Install

Installation from Python package index:

     pip install hls2dash

Installation from source:

     python setup.py install

## Running

Generate Single period MPEG DASH:

     hls-to-dash http://example.com/master.m3u8 > stream.mpd

Generate Multi period MPEG DASH:

     hls-to-dash http://example.com/master.m3u8 --multi > stream.mpd

Rewrap MPEG2 TS segment to fragmented MP4

     ts-to-fmp4 master2500_19274.ts 2500_19274.dash

or when TS segment is on a remote server
     
     ts-to-fmp4 http://example.com/master2500_19274.ts 2500_19274.dash

# Help

## hls-to-dash

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

## ts-to-fmp4

```
usage: ts-to-fmp4 [-h] [--outdir OUTDIR] [--debug] TSFILE OUTPUT

Rewrap a MPEG2 TS segment to a fragmented MP4

positional arguments:
  TSFILE           Path to TS file. Can be a URI or local file.
  OUTPUT           Output file name

optional arguments:
  -h, --help       show this help message and exit
  --outdir OUTDIR  Directory where the fragmented MP4 will be stored. Default is current directory
  --debug          Write debug info to stderr
```
