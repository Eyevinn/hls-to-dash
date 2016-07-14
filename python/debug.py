from __future__ import print_function
import sys

global doDebug
doDebug = False

def log(*args, **kwargs):
    if doDebug:
        print(*args, file=sys.stderr, **kwargs)

