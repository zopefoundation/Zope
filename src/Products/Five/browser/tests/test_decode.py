##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
"""Unit tests for decode module.
"""

def test_processInputs():
    """
    Testing processInputs

      >>> from Products.Five.browser.decode import processInputs
      >>> charsets = ['iso-8859-1']
      >>> class DummyRequest:
      ...     form = {}
      >>> request = DummyRequest()

    Strings are converted to unicode::

      >>> request.form['foo'] = u'f\xf6\xf6'.encode('iso-8859-1')
      >>> processInputs(request, charsets)
      >>> request.form['foo'] == u'f\xf6\xf6'
      True

    Strings in lists are converted to unicode::

      >>> request.form['foo'] = [u'f\xf6\xf6'.encode('iso-8859-1')]
      >>> processInputs(request, charsets)
      >>> request.form['foo'] == [u'f\xf6\xf6']
      True

    Strings in tuples are converted to unicode::

      >>> request.form['foo'] = (u'f\xf6\xf6'.encode('iso-8859-1'),)
      >>> processInputs(request, charsets)
      >>> request.form['foo'] == (u'f\xf6\xf6',)
      True
     
    Ints in lists are not lost::

      >>> request.form['foo'] = [1, 2, 3]
      >>> processInputs(request, charsets)
      >>> request.form['foo'] == [1, 2, 3]
      True
    
    Ints in tuples are not lost::

      >>> request.form['foo'] = (1, 2, 3,)
      >>> processInputs(request, charsets)
      >>> request.form['foo'] == (1, 2, 3)
      True
    
    Mixed lists work:

      >>> request.form['foo'] = [u'f\xf6\xf6'.encode('iso-8859-1'), 2, 3]
      >>> processInputs(request, charsets)
      >>> request.form['foo'] == [u'f\xf6\xf6', 2, 3]
      True
    
    Mixed dicts work:
    
      >>> request.form['foo'] = {'foo': u'f\xf6\xf6'.encode('iso-8859-1'), 'bar': 2}
      >>> processInputs(request, charsets)
      >>> request.form['foo'] == {'foo': u'f\xf6\xf6', 'bar': 2}
      True
    
    Deep recursion works:
    
      >>> request.form['foo'] = [{'foo': u'f\xf6\xf6'.encode('iso-8859-1'), 'bar': 2}, {'foo': u"one", 'bar': 3}]
      >>> processInputs(request, charsets)
      >>> request.form['foo'] == [{'foo': u'f\xf6\xf6', 'bar': 2}, {'foo': u"one", 'bar': 3}]
      True
    
    """

def test_suite():
    from doctest import DocTestSuite
    return DocTestSuite()
