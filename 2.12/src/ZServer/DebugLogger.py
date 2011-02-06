##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""
Logs debugging information about how ZServer is handling requests
and responses. This log can be used to help locate troublesome requests.

The format of a log message is:

    <code> <request id> <time> <data>

where:

    <code> is B for begin, I for received input, A for received output,
    E for sent output.

    <request id> is a unique request id.

    <time> is the local time in ISO 6801 format.

    <data> is the HTTP method and the PATH INFO for B, the size of the
    input for I, the HTTP status code and the size of the output for
    A, or nothing for E.
"""

import time
import logging

from ZServer.BaseLogger import BaseLogger


class DebugLogger(BaseLogger):

    def __init__(self):
        BaseLogger.__init__(self, 'trace')

    def log(self, code, request_id, data=''):
        if not self.logger.handlers:
            return
        # Omitting the second parameter requires Python 2.2 or newer.
        t = time.strftime('%Y-%m-%dT%H:%M:%S')
        message = '%s %s %s %s' % (code, request_id, t, data)
        self.logger.warn(message)


debug_logger = DebugLogger()
log = debug_logger.log
reopen = debug_logger.reopen
