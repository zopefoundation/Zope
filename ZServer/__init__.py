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

import sys

from medusa import asyncore
sys.modules['asyncore'] = asyncore

from medusa.test import max_sockets
CONNECTION_LIMIT=max_sockets.max_select_sockets()

ZSERVER_VERSION='1.1b1'
try:
    import App.version_txt
    ZOPE_VERSION=App.version_txt.version_txt()
except:
    ZOPE_VERSION='experimental'


# Try to poke zLOG default logging into asyncore
# XXX We should probably should do a better job of this,
#     however that would mean that ZServer required zLOG.
#     (Is that really a bad thing?)
try:
    from zLOG import LOG, register_subsystem, BLATHER, INFO, WARNING, ERROR
except ImportError:
    pass
else:
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

import asyncore
from medusa import resolver, logger
from HTTPServer import zhttp_server, zhttp_handler
from PCGIServer import PCGIServer
from FCGIServer import FCGIServer
from FTPServer import FTPServer
from PubCore import setNumberOfThreads
from medusa.monitor import secure_monitor_server

# override the service name in logger.syslog_logger
logger.syslog_logger.svc_name='ZServer'
