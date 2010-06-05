##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Tests for the guarded iterartor.
"""

import unittest

# Persistence system must be initialized.
import ZODB

from AccessControl import ZopeGuards


class SafeIterTestCase(unittest.TestCase):

    # XXX these tests replace the global guard() function in
    # AccessControl.ZopeGuards; this is not the nicest way to check
    # that things work, but avoids making the SafeIter unit tests from
    # testing things other than the guarded iterator itself.  In
    # particular, it avoids testing the actual guard checks, which
    # should be tested separately.

    def setUp(self):
        self.original_guard = ZopeGuards.guard
        ZopeGuards.guard = self.guard
        self.checks = []

    def tearDown(self):
        ZopeGuards.guard = self.original_guard

    def guard(self, container, value, index=None):
        self.checks.append((id(container), value))

    def test_iteration(self):
        seq = [1, 2, 3]
        seqid = id(seq)
        it = ZopeGuards.SafeIter(seq)
        self.assertEqual(list(it), seq)
        self.assertEqual(self.checks, [(seqid, 1),
                                       (seqid, 2),
                                       (seqid, 3)])

    def test_iteration_with_container(self):
        seq = [1, 2, 3]
        container = object()
        contid = id(container)
        it = ZopeGuards.SafeIter(seq, container)
        self.assertEqual(list(it), seq)
        self.assertEqual(self.checks, [(contid, 1),
                                       (contid, 2),
                                       (contid, 3)])


def test_suite():
    return unittest.makeSuite(SafeIterTestCase)
