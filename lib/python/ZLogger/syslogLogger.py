from syslog import syslog_client
import os, string

class syslogLogger:
    """ a syslog Logger """

    def __init__(self):
        if os.environ.has_key('ZSYSLOG_SERVER'):
            (addr, port) = string.split(os.environ['ZSYSLOG_SERVER'], ':')
            self.client = syslog_client((addr, int(port)))
        else:
            self.client = syslog_client()

    def __call__(self, sub, sev, sum, det, err):
        self.client.log(sum)
