##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import time, sys,  os, thread

from zLOG import severity_string, log_time, format_exception

_stupid_dest=None
_stupid_severity=None
_stupid_format=None
_no_stupid_log=[]
format_exception_only=None

class stupidFileLogger:
    """ a stupid File Logger """

    def __call__(self, sub, sev, sum, det, err):
        stupid_log_write(sub, sev, sum, det, err)

def stupid_log_write(subsystem, severity, summary, detail, error):

    # Check where to log
    global _stupid_dest, _stupid_format
    if _stupid_dest is None:
        # EVENT_LOG_FILE is the preferred environment variable, but
        # we accept STUPID_LOG_FILE as well
        eget = os.environ.get
        f = eget('EVENT_LOG_FILE') or eget('STUPID_LOG_FILE')
        if f is not None: # if the envvar exists (might still be null)
            if f: _stupid_dest=open(f,'a')
            else: _stupid_dest=sys.stderr
        elif eget('Z_DEBUG_MODE'):
            _stupid_dest=sys.stderr
        else:
            _stupid_dest=_no_stupid_log

        # EVENT_LOG_FORMAT is the preferred environment variable, but
        # we accept STUPID_LOG_FORMAT as well
        fmt = eget('EVENT_LOG_FORMAT') or eget('STUPID_LOG_FORMAT')

        if fmt is not None:
            _stupid_format = fmt


    # Check id to log
    if _stupid_dest is _no_stupid_log: return

    global _stupid_severity
    if _stupid_severity is None:
        eget = os.environ.get
        # EVENT_LOG_SEVERITY is the preferred environment variable, but
        # we accept STUPID_LOG_SEVERITY as well
        envvar = eget('EVENT_LOG_SEVERITY') or eget('STUPID_LOG_SEVERITY')
        try: _stupid_severity=int(envvar)
        except: _stupid_severity=0

    if severity < _stupid_severity: return

    if _stupid_format is not None:
        fmap = {'time': log_time(),
                'severity': severity_string(severity),
                'subsystem': subsystem,
                'summary': summary,
                'detail': detail,
                'thread': thread.get_ident()
                }
        try:
            s = _stupid_format % fmap
        except:
            failedf, _stupid_format = _stupid_format, None
            _stupid_dest.write("------\n%s %s zLOG Format string error\n"
                               "The EVENT_LOG_FORMAT or STUPID_LOG_FORMAT"
                               "string '%s' caused an error, it wont be used."%
                               (fmap['time'],
                                severity_string(100),
                                failedf)
                               )
        else:
            _stupid_dest.write(s)
    if _stupid_format is None:
        _stupid_dest.write(
            "------\n"
            "%s %s %s %s\n%s"
            %
            (log_time(),
             severity_string(severity),
             subsystem,
             summary,
             detail,
             )
            )

    _stupid_dest.flush()

    if error:
        try:
            _stupid_dest.write(''.join(format_exception(
                error[0], error[1], error[2],
                limit=100)))
        except:
            _stupid_dest.write("%s: %s\n" % error[:2])
    _stupid_dest.flush()
