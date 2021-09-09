import time

class timer:
    def __init__(self):
        self.time_set = 0

    def start(self):
        self.time_set = time.perf_counter()
        return self
    def stop(self):
        return time.perf_counter() - self.time_set

    def reset(self):
        res = self.stop()
        self.time_set = time.perf_counter()
        return res

    def get_elapsed(self):
        return self.stop()
