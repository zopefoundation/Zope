##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""Python Scripts standard utility module

This module provides helpful functions and classes for use in Python
Scripts.  It can be accessed from Python with the statement
"import Products.PythonScripts.standard"
"""

__version__='$Revision: 1.14 $'[11:-2]

from AccessControl import ModuleSecurityInfo, getSecurityManager
security = ModuleSecurityInfo()

security.declarePublic('special_formats', 'whole_dollars',
                       'dollars_and_cents', 'structured_text',
                       'restructured_text',
                       'sql_quote', 'html_quote', 'url_quote',
                       'url_quote_plus', 'newline_to_br',
                       'thousands_commas', 'url_unquote',
                       'url_unquote_plus', 'urlencode')
from DocumentTemplate.DT_Var import special_formats, \
 whole_dollars, dollars_and_cents, structured_text, sql_quote, \
 html_quote, url_quote, url_quote_plus, newline_to_br, thousands_commas, \
 url_unquote, url_unquote_plus, restructured_text
from urllib import urlencode

from Globals import HTML
from AccessControl.DTML import RestrictedDTML

security.declarePublic('DTML')
class DTML(RestrictedDTML, HTML):
    """DTML objects are DocumentTemplate.HTML objects that allow
       dynamic, temporary creation of restricted DTML."""
    def __call__(self, client=None, REQUEST={}, RESPONSE=None, **kw):
        """Render the DTML given a client object, REQUEST mapping,
        Response, and key word arguments."""

        security=getSecurityManager()
        security.addContext(self)
        try:
            return HTML.__call__(self, client, REQUEST, **kw)

        finally: security.removeContext(self)

from ZPublisher.HTTPRequest import record

security.declarePublic('Object')

# We don't expose classes directly to restricted code
class _Object(record):
    _guarded_writes = 1

    def __init__(self, **kw):
        self.update(kw)

    def __setitem__(self, key, value):
        key = str(key)
        if key.startswith('_'):
            raise ValueError, ('Object key %s is invalid. '
                               'Keys may not begin with an underscore.' % `key`)
        self.__dict__[key] = value

    def update(self, d):
        for key in d.keys():
            # Ignore invalid keys, rather than raising an exception.
            try:
                skey = str(key)
            except:
                continue
            if skey==key and not skey.startswith('_'):
                self.__dict__[skey] = d[key]

    def __hash__(self):
        return id(self)

def Object(**kw):
    return _Object(**kw)

security.apply(globals())
