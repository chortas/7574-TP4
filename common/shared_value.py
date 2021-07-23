from threading  import Lock

class SharedValue:
    def __init__(self, value=None):
        self.value = value
        self.gate = Lock()
        self.readers_lock = Lock()
        self.readers = 0

    def _read_acquire(self):
        self.readers_lock.acquire()
        self.readers += 1
        if self.readers == 1:
            self.gate.acquire()
        self.readers_lock.release()

    def _read_release(self):
        if self.readers > 0:
            self.readers_lock.acquire()
            self.readers -= 1
            if self.readers == 0:
                self.gate.release()
            self.readers_lock.release()

    def _write_acquire(self):
        self.gate.acquire()

    def _write_release(self):
        self.gate.release()

    def update(self, value):
        self._write_acquire()
        self.value = value
        self._write_release()

    def read(self):
        self._read_acquire()
        value = self.value
        self._read_release()
        return value
