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

__version__='$Revision: 1.8 $'[11:-2]

from AccessControl import ModuleSecurityInfo, getSecurityManager
security = ModuleSecurityInfo()

security.declarePublic('special_formats', 'whole_dollars',
                       'dollars_and_cents', 'structured_text',
                       'sql_quote', 'html_quote', 'url_quote',
                       'url_quote_plus', 'newline_to_br',
                       'thousands_commas', 'url_unquote',
                       'url_unquote_plus')
from DocumentTemplate.DT_Var import special_formats, \
 whole_dollars, dollars_and_cents, structured_text, sql_quote, \
 html_quote, url_quote, url_quote_plus, newline_to_br, thousands_commas, \
 url_unquote, url_unquote_plus

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
            return apply(HTML.__call__, (self, client, REQUEST), kw)

        finally: security.removeContext(self)

security.apply(globals())

