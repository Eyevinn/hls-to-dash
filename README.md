# Description

This is an open source video streaming packager and toolkit to rewrap live HLS streams to live MPEG DASH streams. 

## Features
 - Generate single period MPEG DASH for live based on an HLS live stream
 - Generate multi period MPEG DASH for live based on an HLS live stream with SCTE35 splicing

# Usage

## Setup
Install Python dependencies

     pip install m3u8    (requires v0.2.10)
     pip install pycurl
     pip install ffprobe

## Single period MPEG DASH
     hls-to-dash http://example.com/master.m3u8 > stream.mpd

## Multi period MPEG DASH
     hls-to-dash http://example.com/master.m3u8 --multi > stream.mpd
