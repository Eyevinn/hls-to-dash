from __future__ import print_function
import sys

doDebug = False
global doDebug

def log(*args, **kwargs):
    if doDebug:
        print(*args, file=sys.stderr, **kwargs)

