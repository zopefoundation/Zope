##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
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
"""

from ZPublisher.HTTPRequest import isCGI_NAMEs
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

def processInputValue(value, charsets):
    """Recursively look for values (e.g. elements of lists, tuples or dicts)
    and attempt to decode.
    """
    
    if isinstance(value, list):
        return [processInputValue(v, charsets) for v in value]
    elif isinstance(value, tuple):
        return tuple([processInputValue(v, charsets) for v in value])
    elif isinstance(value, dict):
        for k, v in value.items():
            value[k] = processInputValue(v, charsets)
        return value
    elif isinstance(value, str):
        return _decode(value, charsets)
    else:
        return value

def processInputs(request, charsets=None):
    """Process the values in request.form to decode strings to unicode, using
    the passed-in list of charsets. If none are passed in, look up the user's
    preferred charsets. The default is to use utf-8.
    """
    
    if charsets is None:
        envadapter = IUserPreferredCharsets(request, None)
        if envadapter is None:
            charsets = ['utf-8']
        else:
            charsets = envadapter.getPreferredCharsets() or ['utf-8']
    
    for name, value in request.form.items():
        if not (name in isCGI_NAMEs or name.startswith('HTTP_')):
            request.form[name] = processInputValue(value, charsets)

def setPageEncoding(request):
    """Set the encoding of the form page via the Content-Type header.
    ZPublisher uses the value of this header to determine how to
    encode unicode data for the browser.
    """
    envadapter = IUserPreferredCharsets(request)
    charsets = envadapter.getPreferredCharsets() or ['utf-8']
    request.RESPONSE.setHeader(
        'Content-Type', 'text/html; charset=%s' % charsets[0])
