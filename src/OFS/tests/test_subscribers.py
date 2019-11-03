##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
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


import logging
import unittest
from io import StringIO


class TestMaybeWarnDeprecated(unittest.TestCase):

    def setUp(self):
        # Make a copy so we can freely modify the contents
        from OFS.subscribers import deprecatedManageAddDeleteClasses
        self._orig_deprecatedManageAddDeleteClasses = (
            deprecatedManageAddDeleteClasses[:])
        self.deprecatedManageAddDeleteClasses = (
            deprecatedManageAddDeleteClasses)
        # Add a class to make sure there is at least one because an empty
        # deprecatedManageAddDeleteClasses list is special cased
        self.deprecatedManageAddDeleteClasses.append(int)
        # Pick up log messages
        self.logfile = StringIO()
        self.log_handler = logging.StreamHandler(self.logfile)
        logging.root.addHandler(self.log_handler)
        self.old_log_level = logging.root.level
        logging.root.setLevel(logging.DEBUG)

    def tearDown(self):
        self.deprecatedManageAddDeleteClasses[:] = (
            self._orig_deprecatedManageAddDeleteClasses)
        logging.root.removeHandler(self.log_handler)
        logging.root.setLevel(self.old_log_level)

    def assertLog(self, class_, expected):
        from OFS.subscribers import maybeWarnDeprecated
        maybeWarnDeprecated(class_(), 'manage_afterAdd')
        self.assertEqual(expected, self.logfile.getvalue())

    def test_method_deprecated(self):
        class Deprecated:
            def manage_afterAdd(self):
                pass
            manage_afterAdd.__five_method__ = True
        self.assertLog(Deprecated, '')

    def test_class_deprecated(self):
        class Deprecated:
            def manage_afterAdd(self):
                pass
        self.deprecatedManageAddDeleteClasses.append(Deprecated)
        self.assertLog(Deprecated, '')

    def test_subclass_deprecated(self):
        class Deprecated:
            def manage_afterAdd(self):
                pass

        class ASubClass(Deprecated):
            pass

        self.deprecatedManageAddDeleteClasses.append(Deprecated)
        self.assertLog(ASubClass, '')

    def test_not_deprecated(self):
        class Deprecated:
            def manage_afterAdd(self):
                pass
        self.assertLog(
            Deprecated,
            'OFS.tests.test_subscribers.Deprecated.manage_afterAdd is '
            'discouraged. You should use event subscribers instead.\n')

    def test_not_deprecated_when_there_are_no_classes(self):
        class Deprecated:
            def manage_afterAdd(self):
                pass
        self.deprecatedManageAddDeleteClasses[:] = []
        self.assertLog(Deprecated, '')
