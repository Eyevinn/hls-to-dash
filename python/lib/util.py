class PT:
    def __init__(self, seconds):
        self.seconds = seconds
    def __str__(self):
        return "PT%dS" % self.seconds

