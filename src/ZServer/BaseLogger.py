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
An abstract logger meant to provide features to the access logger and
the debug logger.
"""

import logging


class BaseLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.propagate = False

    def reopen(self):
        for handler in self.logger.handlers:
            if hasattr(handler, 'reopen') and callable(handler.reopen):
                handler.reopen()
