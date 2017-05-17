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

import unittest


class TestHooks(unittest.TestCase):

    def test_set(self):

        class FauxRequest(object):
            pass

        class FauxEvent(object):
            request = FauxRequest()

        event = FauxEvent()

        from ZPublisher.hooks import set_
        set_(event)

        from zope.globalrequest import getRequest
        self.assertEqual(getRequest(), event.request)

    def test_clear(self):

        class FauxRequest(object):
            pass

        class FauxEvent(object):
            request = FauxRequest()

        event = FauxEvent()

        from zope.globalrequest import setRequest
        setRequest(event.request)

        from ZPublisher.hooks import clear
        clear(event)

        from zope.globalrequest import getRequest
        self.assertEqual(getRequest(), None)
