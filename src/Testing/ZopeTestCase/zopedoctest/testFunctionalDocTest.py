##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
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

$Id$
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from unittest import TestSuite
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import FunctionalDocTestSuite
from Testing.ZopeTestCase import FunctionalDocFileSuite

installProduct('PythonScripts')


def setUp(self):
    '''This method will run after the test_class' setUp.

    >>> print http(r"""
    ... GET /test_folder_1_/index_html HTTP/1.1
    ... """)
    HTTP/1.1 200 OK
    Content-Length: 5
    Content-Type: text/plain; charset=...
    <BLANKLINE>
    index

    >>> foo
    1
    '''
    self.folder.addDTMLDocument('index_html', file='index')

    self.folder.manage_addProduct['PythonScripts'].manage_addPythonScript('script')
    self.folder.script.ZPythonScript_edit(params='a=0', body='return a+1')

    change_title = '''<dtml-call "manage_changeProperties(title=REQUEST.get('title'))">'''
    self.folder.addDTMLMethod('change_title', file=change_title)

    set_cookie = '''<dtml-call "REQUEST.RESPONSE.setCookie('cookie_test', 'OK')">'''
    self.folder.addDTMLMethod('set_cookie', file=set_cookie)

    show_cookies = '''<dtml-in "REQUEST.cookies.keys()">
<dtml-var sequence-item>: <dtml-var "REQUEST.cookies[_['sequence-item']]">
</dtml-in>'''
    self.folder.addDTMLMethod('show_cookies', file=show_cookies)

    self.globs['foo'] = 1


def test_suite():
    return TestSuite((
        FunctionalDocTestSuite(setUp=setUp),
        FunctionalDocFileSuite('FunctionalDocTest.txt', setUp=setUp),
    ))

if __name__ == '__main__':
    framework()

