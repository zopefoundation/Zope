##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Example functional doctest
"""
import unittest

from Testing.ZopeTestCase import FunctionalDocFileSuite
from Testing.ZopeTestCase import FunctionalDocTestSuite


class HTTPHeaderOutputTests(unittest.TestCase):

    def _getTargetClass(self):
        from Testing.ZopeTestCase.zopedoctest.functional import \
            HTTPHeaderOutput
        return HTTPHeaderOutput

    def _makeOne(self, protocol, omit):
        return self._getTargetClass()(protocol, omit)

    def test_ctor(self):
        hho = self._makeOne('HTTP/1.0', ())
        self.assertEqual(hho.protocol, 'HTTP/1.0')
        self.assertEqual(hho.omit, ())
        self.assertEqual(hho.status, '200')
        self.assertEqual(hho.reason, 'OK')
        self.assertEqual(hho.headers, {})
        self.assertEqual(hho.headersl, [])

    def test_setResponseStatus(self):
        hho = self._makeOne('HTTP/1.0', ())
        hho.setResponseStatus('401', 'Unautnorized')
        self.assertEqual(hho.status, '401')
        self.assertEqual(hho.reason, 'Unautnorized')

    def test_setResponseHeaders_no_omit(self):
        hho = self._makeOne('HTTP/1.0', ())
        hho.setResponseHeaders({'Content-Type': 'text/html'})
        self.assertEqual(hho.headers, {'Content-Type': 'text/html'})
        self.assertEqual(hho.headersl, [])

    def test_setResponseHeaders_w_omit(self):
        hho = self._makeOne('HTTP/1.0', ('content-type',))
        hho.setResponseHeaders({'Content-Type': 'text/html'})
        self.assertEqual(hho.headers, {})
        self.assertEqual(hho.headersl, [])

    def test_appendResponseHeaders_no_omit_tuples(self):
        hho = self._makeOne('HTTP/1.0', ())
        hho.appendResponseHeaders([('Content-Type', 'text/html')])
        self.assertEqual(hho.headers, {})
        self.assertEqual(hho.headersl, [('Content-Type', 'text/html')])

    def test_appendResponseHeaders_no_omit_strings(self):
        # Some Zope versions passed around headers as lists of strings.
        hho = self._makeOne('HTTP/1.0', ())
        hho.appendResponseHeaders([('Content-Type: text/html')])
        self.assertEqual(hho.headers, {})
        self.assertEqual(hho.headersl, [('Content-Type', 'text/html')])

    def test_appendResponseHeaders_w_omit(self):
        hho = self._makeOne('HTTP/1.0', ('content-type',))
        hho.appendResponseHeaders([('Content-Type', 'text/html')])
        self.assertEqual(hho.headers, {})
        self.assertEqual(hho.headersl, [])

    def test___str___no_headers(self):
        hho = self._makeOne('HTTP/1.0', ('content-type',))
        self.assertEqual(str(hho), 'HTTP/1.0 200 OK')

    def test___str___w_headers(self):
        hho = self._makeOne('HTTP/1.0', ('content-type',))
        hho.headers['Content-Type'] = 'text/html'
        hho.headersl.append(('Content-Length', '23'))
        self.assertEqual(str(hho),
                         'HTTP/1.0 200 OK\n'
                         'Content-Length: 23\n'
                         'Content-Type: text/html')


SHOW_COOKIES_DTML = '''\
<dtml-in "REQUEST.cookies.keys()">
<dtml-var sequence-item>: <dtml-var "REQUEST.cookies[_['sequence-item']]">
</dtml-in>'''


def setUp(self):
    '''This method will run after the test_class' setUp.

    >>> http = http  # NOQA: F821
    >>> response = http(r"""
    ... GET /test_folder_1_/index_html HTTP/1.1
    ... """)
    >>> response.status
    200
    >>> response.headers == {
    ...     'content-length': '5', 'content-type': 'text/plain; charset=utf-8'}
    True
    >>> response.getBody() == b'index'
    True

    >>> foo  # NOQA: F821
    1
    '''
    from Testing.ZopeTestCase.testFunctional import CHANGE_TITLE_DTML
    from Testing.ZopeTestCase.testFunctional import SET_COOKIE_DTML

    self.folder.addDTMLDocument('index_html', file='index')
    self.folder.addDTMLMethod('change_title', file=CHANGE_TITLE_DTML)
    self.folder.addDTMLMethod('set_cookie', file=SET_COOKIE_DTML)
    self.folder.addDTMLMethod('show_cookies', file=SHOW_COOKIES_DTML)
    self.globs['foo'] = 1


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(
            HTTPHeaderOutputTests),
        FunctionalDocTestSuite(setUp=setUp),
        FunctionalDocFileSuite('FunctionalDocTest.txt', setUp=setUp),
    ))
