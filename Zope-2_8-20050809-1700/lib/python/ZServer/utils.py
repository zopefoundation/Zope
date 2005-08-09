##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

""" A set of utility routines used by asyncore initialization """

def getZopeVersion():
    import App.version_txt
    return App.version_txt.version_txt()

def patchAsyncoreLogger():
    # Poke zLOG default logging into asyncore to send
    # messages to zLOG instead of medusa logger
    from zLOG import LOG, register_subsystem, BLATHER, INFO, WARNING, ERROR
    register_subsystem('ZServer')
    severity={'info':INFO, 'warning':WARNING, 'error': ERROR}

    def log_info(self, message, type='info'):
        if message[:14]=='adding channel' or \
           message[:15]=='closing channel' or \
           message == 'Computing default hostname':
            LOG('ZServer', BLATHER, message)
        else:
            LOG('ZServer', severity[type], message)

    import asyncore
    asyncore.dispatcher.log_info=log_info

# A routine to try to arrange for request sockets to be closed
# on exec. This makes it easier for folks who spawn long running
# processes from Zope code. Thanks to Dieter Maurer for this.
try:
    import fcntl

    def requestCloseOnExec(sock):
        try:
            fcntl.fcntl(sock.fileno(), fcntl.F_SETFD, fcntl.FD_CLOEXEC)
        except: # XXX What was this supposed to catch?
            pass

except (ImportError, AttributeError):

    def requestCloseOnExec(sock):
        pass

def patchSyslogServiceName():
    from medusa import logger
    # override the service name in logger.syslog_logger
    logger.syslog_logger.svc_name='ZServer'
