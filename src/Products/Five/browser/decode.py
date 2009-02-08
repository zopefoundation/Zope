##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
""" Utility functions for decoding browser input and setting the output
    encoding.

$Id$
"""

from zope.publisher.browser import isCGI_NAME
from zope.i18n.interfaces import IUserPreferredCharsets

# taken and adapted from zope.publisher.browser.BrowserRequest
def _decode(text, charsets):
    """Try to decode the text using one of the available charsets.
    """
    for charset in charsets:
        try:
            text = unicode(text, charset)
            break
        except UnicodeError:
            pass
    return text

def processInputs(request, charsets=None):
    if charsets is None:
        envadapter = IUserPreferredCharsets(request)
        charsets = envadapter.getPreferredCharsets() or ['utf-8']

    for name, value in request.form.items():
        if not (isCGI_NAME(name) or name.startswith('HTTP_')):
            if isinstance(value, str):
                request.form[name] = _decode(value, charsets)
            elif isinstance(value, list):
                request.form[name] = [ _decode(val, charsets)
                                       for val in value
                                       if isinstance(val, str) ]
            elif isinstance(value, tuple):
                request.form[name] = tuple([ _decode(val, charsets)
                                             for val in value
                                             if isinstance(val, str) ])

def setPageEncoding(request):
    """Set the encoding of the form page via the Content-Type header.
    ZPublisher uses the value of this header to determine how to
    encode unicode data for the browser.
    """
    envadapter = IUserPreferredCharsets(request)
    charsets = envadapter.getPreferredCharsets() or ['utf-8']
    request.RESPONSE.setHeader(
        'Content-Type', 'text/html; charset=%s' % charsets[0])
