from syslog import syslog_client
import os, string

class syslogLogger:
    """ a syslog Logger """

    def __init__(self):
        if os.environ.has_key('ZSYSLOG_SERVER'):
            (addr, port) = string.split(os.environ['ZSYSLOG_SERVER'], ':')
            self.client = syslog_client((addr, int(port)))
            self.on = 1
        elif os.environ.has_key('ZSYSLOG'):
            self.client = syslog_client()
            self.on = 1
        else:
            self.on = 0

    def __call__(self, sub, sev, sum, det, err):
        if on:
            self.client.log(sum)
