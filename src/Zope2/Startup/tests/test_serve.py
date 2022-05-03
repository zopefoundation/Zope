##############################################################################
#
# Copyright (c) 2019 Zope Foundation and Contributors.
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

import io
import sys
import unittest


class TestFunctions(unittest.TestCase):

    def test_parse_vars(self):
        from Zope2.Startup.serve import parse_vars

        input_data = []
        self.assertEqual(parse_vars(input_data), {})

        # There is now stripping of whitespace
        input_data = ['foo = bar', 'abc=xyz']
        self.assertEqual(parse_vars(input_data),
                         {'foo ': ' bar', 'abc': 'xyz'})

        input_data = ['in:valid']
        self.assertRaises(ValueError, parse_vars, input_data)

    def test__getpathsec(self):
        from Zope2.Startup.serve import _getpathsec

        self.assertEqual(_getpathsec('', ''), ('', 'main'))
        self.assertEqual(_getpathsec('name', ''), ('name', 'main'))
        self.assertEqual(_getpathsec('name#name2', ''), ('name', 'name2'))
        self.assertEqual(_getpathsec('name1', 'name2'), ('name1', 'name2'))


class TestServeCommand(unittest.TestCase):

    def _makeOne(self, argv=[], quiet=False):
        from Zope2.Startup.serve import ServeCommand
        return ServeCommand(argv, quiet=quiet)

    def _getFileLike(self):
        return io.StringIO()

    def test_defaults(self):
        srv = self._makeOne()
        self.assertEqual(srv.args, [])
        self.assertIsNone(srv.options.app_name)
        self.assertIsNone(srv.options.server)
        self.assertIsNone(srv.options.server_name)
        self.assertEqual(srv.options.verbose, 1)
        self.assertIsNone(srv.options.debug)
        self.assertIsNone(srv.options.debug_exceptions)

    def test_nondefaults(self):
        args = ['command', '-n', 'myapp', '-s', 'mywsgi',
                '--server-name=myserver', '-vvvv', '-d', '-e']
        srv = self._makeOne(args)
        self.assertEqual(srv.args, [])
        self.assertEqual(srv.options.app_name, 'myapp')
        self.assertEqual(srv.options.server, 'mywsgi')
        self.assertEqual(srv.options.server_name, 'myserver')
        self.assertEqual(srv.options.verbose, 5)
        self.assertTrue(srv.options.debug)
        self.assertTrue(srv.options.debug_exceptions)

    def test_quiet(self):
        args = ['command', '-q']
        srv = self._makeOne(args)
        self.assertEqual(srv.options.verbose, 0)

        srv = self._makeOne([], quiet=True)
        self.assertEqual(srv.options.verbose, 0)

    def test_out_notquiet(self):
        old_stdout = sys.stdout

        new_stdout = self._getFileLike()
        sys.stdout = new_stdout

        try:
            srv = self._makeOne(quiet=False)
            srv.out('output')
            self.assertEqual(new_stdout.getvalue().strip(), 'output')
        finally:
            sys.stdout = old_stdout

    def test_out_quiet(self):
        old_stdout = sys.stdout
        new_stdout = self._getFileLike()
        sys.stdout = new_stdout
        try:
            srv = self._makeOne(quiet=True)
            srv.out('output')
            self.assertEqual(new_stdout.getvalue().strip(), '')
        finally:
            sys.stdout = old_stdout

    def test_remaining_options(self):
        args = ['command', 'somekey=somevalue', 'foo=bar']
        srv = self._makeOne(args)
        self.assertEqual(srv.args, ['somekey=somevalue', 'foo=bar'])
