##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

""" A set of utility routines used by asyncore initialization """

import sys

import pkg_resources

_version_string = None


def _prep_version_data():
    global _version_string
    if _version_string is None:
        v = sys.version_info
        pyver = "python %d.%d.%d, %s" % (v[0], v[1], v[2], sys.platform)
        dist = pkg_resources.get_distribution('Zope2')
        _version_string = "%s, %s" % (dist.version, pyver)


def getZopeVersion():
    _prep_version_data()
    return '(%s)' % _version_string


def patchAsyncoreLogger():
    # Poke the Python logging module into asyncore to send messages to logging
    # instead of medusa logger

    from logging import getLogger
    LOG = getLogger('ZServer')

    def log_info(self, message, type='info'):
        if message[:44]=='uncaptured python exception, closing channel' or \
           message == 'Computing default hostname':
            LOG.debug(message)
        else:
            getattr(LOG, type)(message)

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
