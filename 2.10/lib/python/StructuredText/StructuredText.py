##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Alias module for StructuredTextClassic compatibility which makes
use of StructuredTextNG"""
import re
from zope.structuredtext import stx2html as HTML
from zope.structuredtext import stx2htmlWithReferences as html_with_references
StructuredText = HTML

from zope.deprecation import deprecated
deprecated(("HTML, StructuredText"),
           'The StructuredText package is deprecated and will be removed '
           'in Zope 2.12. Use zope.structuredtext.stx2html instead.')
deprecated("html_with_references",
           'The StructuredText package is deprecated and will be removed '
           'in Zope 2.12. Use zope.structuredtext.stx2htmlWithReferences '
           'instead.')

def html_quote(v,
               character_entities=(
                       (re.compile('&'), '&amp;'),
                       (re.compile("<"), '&lt;' ),
                       (re.compile(">"), '&gt;' ),
                       (re.compile('"'), '&quot;')
                       )): #"
    text=str(v)
    for re,name in character_entities:
        text=re.sub(name,text)
    return text

if __name__=='__main__':
    import getopt

    opts,args = getopt.getopt(sys.argv[1:],'',[])

    for k,v in opts:
        pass


    for f in args:
        print HTML(open(f).read())
