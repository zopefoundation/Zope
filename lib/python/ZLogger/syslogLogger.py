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
from syslog import syslog_client, LOG_ALERT, LOG_ERR, LOG_WARNING, LOG_NOTICE
from syslog import LOG_INFO, LOG_DEBUG

import os, traceback

pid_str='[%s]: ' % os.getpid()


class syslogLogger:
    """ a syslog Logger """

    def __init__(self):
        if os.environ.has_key('ZSYSLOG_SERVER'):
            (addr, port) = os.environ['ZSYSLOG_SERVER'].split(':')
            self.client = syslog_client((addr, int(port)))
            self.on = 1
        elif os.environ.has_key('ZSYSLOG'):
            self.client = syslog_client(os.environ['ZSYSLOG'])
            self.on = 1
        else:
            self.on = 0

    def __call__(self, sub, sev, sum, det, err):

        if sev >= 0:
            if sev >= 200:
                if sev >= 300:
                    sev=LOG_ALERT
                else:
                    sev=LOG_ERR
            else:
                if sev >= 100:
                    sev=LOG_WARNING
                else:
                    sev=LOG_NOTICE
        else:
            if sev >= -100:
                sev=LOG_INFO
            else:
                sev=LOG_DEBUG
        if err:
            try: sum = sum + ' : ' + traceback.format_exception_only(
                                                     err[0], err[1]
                                                     )[0]
            except: pass
        if self.on:
            self.client.log(sub + pid_str + sum, priority=sev)
