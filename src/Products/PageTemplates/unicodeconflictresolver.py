##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Unicode conflict resolution.
"""

import sys

import ZPublisher.HTTPRequest
from Acquisition import aq_get
from Products.PageTemplates.interfaces import IUnicodeEncodingConflictResolver
from zope.i18n.interfaces import IUserPreferredCharsets
from zope.interface import implementer


default_encoding = sys.getdefaultencoding()


@implementer(IUnicodeEncodingConflictResolver)
class DefaultUnicodeEncodingConflictResolver:
    """ This resolver implements the old-style behavior and will
        raise an exception in case of the string 'text' can't be converted
        properly to unicode.
    """

    def resolve(self, context, text, expression):
        if isinstance(text, str):
            return text
        return text.decode('ascii')


DefaultUnicodeEncodingConflictResolver = \
    DefaultUnicodeEncodingConflictResolver()


@implementer(IUnicodeEncodingConflictResolver)
class Z2UnicodeEncodingConflictResolver:
    """ This resolver tries to lookup the encoding from the
        'default-zpublisher-encoding' setting in the Zope configuration
        file and defaults to the old ZMI encoding iso-8859-15.
    """

    def __init__(self, mode='strict'):
        self.mode = mode

    def resolve(self, context, text, expression):
        if isinstance(text, str):
            return text

        try:
            return text.decode('ascii')
        except UnicodeDecodeError:
            encoding = ZPublisher.HTTPRequest.default_encoding
            try:
                return text.decode(encoding, errors=self.mode)
            except UnicodeDecodeError:
                # finally try the old management_page_charset default
                return text.decode('iso-8859-15', errors=self.mode)


@implementer(IUnicodeEncodingConflictResolver)
class PreferredCharsetResolver:
    """ A resolver that tries use the encoding information
        from the HTTP_ACCEPT_CHARSET header.
    """

    def resolve(self, context, text, expression):
        if isinstance(text, str):
            return text

        request = aq_get(context, 'REQUEST', None)

        # Deal with the fact that a REQUEST is not always available.
        # In this case fall back to the encoding of the ZMI and the
        # Python default encoding.

        if request is None:
            charsets = [ZPublisher.HTTPRequest.default_encoding,
                        default_encoding]
        else:
            # charsets might by cached within the request
            charsets = getattr(request, '__zpt_available_charsets', None)

        # No uncached charsets found: investigate the HTTP_ACCEPT_CHARSET
        # header. This code is only called if 'context' has a request
        # object. The condition is true because otherwise 'charsets' contains
        # at least the default encoding of Python.
        if charsets is None:

            charsets = list()

            # add Python's default encoding as last fallback
            charsets.append(default_encoding)

            # include the charsets based on the HTTP_ACCEPT_CHARSET
            # header
            charsets = IUserPreferredCharsets(
                request).getPreferredCharsets() + charsets

            # cache list of charsets
            request.__zpt_available_charsets = charsets

        for enc in charsets:
            if enc == '*':
                continue

            try:
                return text.decode(enc)
            except (LookupError, UnicodeDecodeError):
                pass

        # FIXME: Shouldn't this raise an Exception or signal an error somehow?
        return text


StrictUnicodeEncodingConflictResolver = \
    Z2UnicodeEncodingConflictResolver('strict')
ReplacingUnicodeEncodingConflictResolver = \
    Z2UnicodeEncodingConflictResolver('replace')
IgnoringUnicodeEncodingConflictResolver = \
    Z2UnicodeEncodingConflictResolver('ignore')
PreferredCharsetResolver = PreferredCharsetResolver()
