from threading import Timer

"""
Found at https://stackoverflow.com/questions/12435211/threading-timer-repeat-function-every-n-seconds

Code by right2clicky, based on Hans Then's original example
"""

class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)