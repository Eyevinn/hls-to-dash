# Copyright 2016 Eyevinn Technology. All rights reserved
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.
# Author: Jonas Birme (Eyevinn Technology)


class PT:
    def __init__(self, seconds):
        self.seconds = seconds
    def __str__(self):
        return "PT%fS" % self.seconds

