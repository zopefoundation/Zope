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

import sys, os

# HACKERY to get around asyncore issues. This ought to go away! We're
# currently using the Python 2.2 asyncore bundled with Zope to override
# brokenness in the Python 2.1 version. We need to do some funny business
# to make this work, as a 2.2-ism crept into the asyncore code.
if os.name == 'posix':
    import fcntl
    if not hasattr(fcntl, 'F_GETFL'):
        import FCNTL
        fcntl.F_GETFL = FCNTL.F_GETFL
        fcntl.F_SETFL = FCNTL.F_SETFL

from medusa import asyncore
sys.modules['asyncore'] = asyncore



from medusa.test import max_sockets
CONNECTION_LIMIT=max_sockets.max_select_sockets()

ZSERVER_VERSION='1.1b1'
try:
    import App.version_txt, App.FindHomes
    ZOPE_VERSION=App.version_txt.version_txt()
except:
    ZOPE_VERSION='experimental'


# Try to poke zLOG default logging into asyncore
# XXX We should probably should do a better job of this,
#     however that would mean that ZServer required zLOG.
try:
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
except:
    pass

# A routine to try to arrange for request sockets to be closed
# on exec. This makes it easier for folks who spawn long running
# processes from Zope code. Thanks to Dieter Maurer for this.
try:
    import fcntl, FCNTL
    FCNTL.F_SETFD; FCNTL.FD_CLOEXEC
    def requestCloseOnExec(sock):
        try:    fcntl.fcntl(sock.fileno(), FCNTL.F_SETFD, FCNTL.FD_CLOEXEC)
        except: pass

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
