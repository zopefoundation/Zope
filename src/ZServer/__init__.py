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

import utils

from Zope2.Startup.config import (  # NOQA
    ZSERVER_CONNECTION_LIMIT as CONNECTION_LIMIT,
    ZSERVER_EXIT_CODE as exit_code,
    ZSERVER_LARGE_FILE_THRESHOLD as LARGE_FILE_THRESHOLD,
    setNumberOfThreads,
)

# the ZServer version number
ZSERVER_VERSION = '1.1'

# the Zope version string
ZOPE_VERSION = utils.getZopeVersion()

# backwards compatibility aliases
from utils import requestCloseOnExec
import asyncore
from medusa import resolver, logger
from HTTPServer import zhttp_server, zhttp_handler
from PCGIServer import PCGIServer
from FCGIServer import FCGIServer
from FTPServer import FTPServer
from medusa.monitor import secure_monitor_server

# we need to patch asyncore's dispatcher class with a new
# log_info method so we see medusa messages in the zLOG log
utils.patchAsyncoreLogger()

# we need to patch the 'service name' of the medusa syslog logger
utils.patchSyslogServiceName()
