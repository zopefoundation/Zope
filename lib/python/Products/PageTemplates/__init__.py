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
"""Package wrapper for Page Templates

This wrapper allows the Page Template modules to be segregated in a
separate package.

$Id$
"""

# Placeholder for Zope Product data
misc_ = {}

# import ZTUtils in order to make i importable through
# ZopeGuards.load_module() where an importable modules must be
# available in sys.modules
import ZTUtils


def initialize(context):
    # Import lazily, and defer initialization to the module
    import ZopePageTemplate
    ZopePageTemplate.initialize(context)


# HACK!!!
# We need to monkeypatch the parseString method of the Zope 3 
# XMLParser since the internal ZPT representation uses unicode
# however the XMLParser (using Expat) can only deal with standard
# Python strings. However we won't and can't convert directly
# to UTF-8 within the ZPT wrapper code. 
# Unicode support for (this issue) should be directly added
# to zope.tal.xmlparser however this requires a new Zope 3.3.X
# release. For now we fix it here.

from zope.tal.xmlparser import XMLParser
import logging

def parseString(self, s):
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    self.parser.Parse(s, 1)

XMLParser.parseString = parseString
logging.info('Monkeypatching zope.tal.xmlparser.XMLParser.parseString()')
