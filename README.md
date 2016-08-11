# Description

This is an open source video streaming packager and toolkit to rewrap live HLS streams to live MPEG DASH streams. 

# Usage

## Single period MPEG DASH
     hls-to-dash http://example.com/master.m3u8 > stream.mpd

## Multi period MPEG DASH
     hls-to-dash http://example.com/master.m3u8 --multi > stream.mpd
