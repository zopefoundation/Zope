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

import sys
import utils

#########################################################
### declarations used by external packages

# the exit code used to exit a Zope process cleanly
exit_code = 0

# the ZServer version number
ZSERVER_VERSION = '1.1'

# the maximum number of incoming connections to ZServer
CONNECTION_LIMIT = 1000 # may be reset by max_listen_sockets handler in Zope

# request bigger than this size get saved into a
# temporary file instead of being read completely into memory
LARGE_FILE_THRESHOLD = 1 << 19 # may be reset by large_file_threshold
                               # handler in Zope

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
from PubCore import setNumberOfThreads
from medusa.monitor import secure_monitor_server

### end declarations
##########################################################

# we need to patch asyncore's dispatcher class with a new
# log_info method so we see medusa messages in the zLOG log
utils.patchAsyncoreLogger()

# we need to patch the 'service name' of the medusa syslog logger
utils.patchSyslogServiceName()


