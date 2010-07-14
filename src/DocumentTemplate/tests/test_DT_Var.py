##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Tests for functions and classes in DT_Var.

$Id$
"""

import unittest, doctest

class TestNewlineToBr(doctest.DocTestCase):

    def test_newline_to_br(self):
        r"""
        newline_to_br should work identically with either DOS-style or
        Unix-style newlines.

        >>> from DocumentTemplate import DT_Var
        >>> text = '''
        ... line one
        ... line two
        ...
        ... line three
        ... '''
        >>> print DT_Var.newline_to_br(text)
        <br />
        line one<br />
        line two<br />
        <br />
        line three<br />
        <BLANKLINE>
        
        >>> dos = text.replace('\n', '\r\n')
        >>> DT_Var.newline_to_br(text) == DT_Var.newline_to_br(dos)
        True
        """


    def test_newline_to_br_tainted(self):
        """
        >>> from DocumentTemplate import DT_Var
        >>> text = '''
        ... <li>line one</li>
        ... <li>line two</li>
        ... '''
        >>> from ZPublisher.TaintedString import TaintedString
        >>> tainted = TaintedString(text)
        >>> print DT_Var.newline_to_br(tainted)
        <br />
        &lt;li&gt;line one&lt;/li&gt;<br />
        &lt;li&gt;line two&lt;/li&gt;<br />
        <BLANKLINE>

        """


class TestUrlQuoting(unittest.TestCase):

    def test_url_quoting(self):
        from DocumentTemplate.DT_Var import url_quote
        from DocumentTemplate.DT_Var import url_unquote
        unicode_value = u'G\xfcnther M\xfcller'
        quoted_unicode_value = u'G%C3%BCnther%20M%C3%BCller'
        utf8_value = unicode_value.encode('UTF-8')
        quoted_utf8_value = 'G%C3%BCnther%20M%C3%BCller'

        self.assertEquals(url_quote(unicode_value), quoted_unicode_value)
        self.assertEquals(url_quote(utf8_value), quoted_utf8_value)
        
        self.assertEquals(url_unquote(quoted_unicode_value), unicode_value)
        self.assertEquals(url_unquote(quoted_utf8_value), utf8_value)


    def test_url_quoting_plus(self):
        from DocumentTemplate.DT_Var import url_quote_plus
        from DocumentTemplate.DT_Var import url_unquote_plus
        unicode_value = u'G\xfcnther M\xfcller'
        quoted_unicode_value = u'G%C3%BCnther+M%C3%BCller'
        utf8_value = unicode_value.encode('UTF-8')
        quoted_utf8_value = 'G%C3%BCnther+M%C3%BCller'

        self.assertEquals(url_quote_plus(unicode_value), quoted_unicode_value)
        self.assertEquals(url_quote_plus(utf8_value), quoted_utf8_value)
        
        self.assertEquals(url_unquote_plus(quoted_unicode_value), unicode_value)
        self.assertEquals(url_unquote_plus(quoted_utf8_value), utf8_value)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite())
    suite.addTest(unittest.makeSuite(TestUrlQuoting))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
