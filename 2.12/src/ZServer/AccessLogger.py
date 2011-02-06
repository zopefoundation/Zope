##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
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
A logging module which handles ZServer access log messages.

This depends on Vinay Sajip's PEP 282 logging module.
"""

from ZServer.BaseLogger import BaseLogger


class AccessLogger(BaseLogger):

    def __init__(self):
        BaseLogger.__init__(self, 'access')

    def log(self, message):
        if not self.logger.handlers: # don't log if we have no handlers
            return
        if message.endswith('\n'):
            message = message[:-1]
        self.logger.warn(message)

access_logger = AccessLogger()
