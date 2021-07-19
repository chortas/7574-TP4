import fcntl

class FileLock:
    def acquire_readonly(self, filepath):
        lockfile = open(filepath, 'r')
        fcntl.lockf(lockfile, fcntl.LOCK_SH)
        return lockfile

    def acquire_writeonly(self, filepath, type='w'):
        lockfile = open(filepath, type)
        fcntl.lockf(lockfile, fcntl.LOCK_EX)
        return lockfile

    def release(self, lock):
        fcntl.flock(lock, fcntl.LOCK_UN)
