##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Functional tests for exception handling.
"""

import unittest
from Testing.ZopeTestCase import FunctionalDocFileSuite

from OFS.SimpleItem import SimpleItem


class ExceptionRaiser1(SimpleItem):

    def index_html(self):
        """DOCSTRING
        """
        raise self.exception


class ExceptionRaiser2(ExceptionRaiser1):

    __roles__ = ()


class ExceptionRaiser3(SimpleItem):

    def index_html(self):
        return 'NO DOCSTRING'


def test_suite():
    return unittest.TestSuite([
        FunctionalDocFileSuite('exception_handling.txt',
            globs={'ExceptionRaiser1': ExceptionRaiser1,
                   'ExceptionRaiser2': ExceptionRaiser2,
                   'ExceptionRaiser3': ExceptionRaiser3,}),
        ])
