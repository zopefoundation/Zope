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

from warnings import warn

from six import binary_type
from six import text_type

from zope.i18n.interfaces import IUserPreferredCharsets
from ZPublisher.HTTPRequest import isCGI_NAMEs


def _decode(text, charsets):
    """Try to decode the text using one of the available charsets.
    """
    # taken and adapted from zope.publisher.browser.BrowserRequest
    for charset in charsets:
        try:
            text = text_type(text, charset)
            break
        except UnicodeError:
            pass
    return text


def processInputValue(value, charsets):
    """Recursively look for values (e.g. elements of lists, tuples or dicts)
    and attempt to decode.
    """
    warn(u'processInputValue() is deprecated and will be removed in Zope '
         u'5.0.',
         DeprecationWarning, stacklevel=2)

    if isinstance(value, list):
        return [processInputValue(v, charsets) for v in value]
    elif isinstance(value, tuple):
        return tuple([processInputValue(v, charsets) for v in value])
    elif isinstance(value, dict):
        for k, v in list(value.items()):
            value[k] = processInputValue(v, charsets)
        return value
    elif isinstance(value, binary_type):
        return _decode(value, charsets)
    else:
        return value


def processInputs(request, charsets=None):
    """Process the values in request.form to decode binary_type to text_type,
    using the passed-in list of charsets. If none are passed in, look up the
    user's preferred charsets. The default is to use utf-8.
    """
    warn(u'processInputs() is deprecated and will be removed in Zope 5.0. If '
         u'your view implements IBrowserPage, similar processing is now '
         u'executed automatically.',
         DeprecationWarning, stacklevel=2)

    if charsets is None:
        envadapter = IUserPreferredCharsets(request, None)
        if envadapter is None:
            charsets = ['utf-8']
        else:
            charsets = envadapter.getPreferredCharsets() or ['utf-8']

    for name, value in list(request.form.items()):
        if not (name in isCGI_NAMEs or name.startswith('HTTP_')):
            request.form[name] = processInputValue(value, charsets)


def setPageEncoding(request):
    """Set the encoding of the form page via the Content-Type header.
    ZPublisher uses the value of this header to determine how to
    encode unicode data for the browser.
    """
    warn(u'setPageEncoding() is deprecated and will be removed in Zope 5.0. '
         u'It is recommended to let the ZPublisher use the default_encoding. '
         u'Please consider setting default-zpublisher-encoding to utf-8.',
         DeprecationWarning, stacklevel=2)
    envadapter = IUserPreferredCharsets(request)
    charsets = envadapter.getPreferredCharsets() or ['utf-8']
    request.RESPONSE.setHeader(
        'Content-Type', 'text/html; charset=%s' % charsets[0])
