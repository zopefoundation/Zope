import stupidFileLogger
import syslogLogger

from zLOG import *

loggers = (stupidFileLogger.stupidFileLogger(), syslogLogger.syslogLogger(),)

def log_write(subsystem, severity, summary, detail, error):
    """ Hook into the logging system

    The actual logic to determine what log messages go where will go
    here.  For now, everything goes to all loggers.
    """

    for logger in loggers:
        logger(subsystem, severity, summary, detail, error)
