class FileLogger:
    """ a File Logger

    This is just a stub, FileLogger should be smarter than
    stupidFileLogger, but for the moment it's completely brain dead.
    """

    def __init__(self):
        pass

    def __call__(self, sub, sev, sum, det, err):
        print 'syslogger %s, %s, %s, %s, %s, %s' % (self, sub, sev, sum, det, err)
