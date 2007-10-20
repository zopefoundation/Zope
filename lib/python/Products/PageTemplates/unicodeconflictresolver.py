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

import sys

from zope.interface import implements
from zope.i18n.interfaces import IUserPreferredCharsets

from Products.PageTemplates.interfaces import IUnicodeEncodingConflictResolver

default_encoding = sys.getdefaultencoding()

class DefaultUnicodeEncodingConflictResolver:
    """ This resolver implements the old-style behavior and will 
        raise an exception in case of the string 'text' can't be converted
        propertly to unicode.
    """

    implements(IUnicodeEncodingConflictResolver)

    def resolve(self, context, text, expression):
        return unicode(text)

DefaultUnicodeEncodingConflictResolver = DefaultUnicodeEncodingConflictResolver()


class Z2UnicodeEncodingConflictResolver:
    """ This resolver tries to lookup the encoding from the 
        'management_page_charset' property and defaults to 
        sys.getdefaultencoding().
    """

    implements(IUnicodeEncodingConflictResolver)

    def __init__(self, mode='strict'):
        self.mode = mode

    def resolve(self, context, text, expression):

        try:
            return unicode(text)
        except UnicodeDecodeError:
            encoding = getattr(context, 'management_page_charset', default_encoding)
            return unicode(text, encoding, self.mode)

class PreferredCharsetResolver:
    """ A resolver that tries use the encoding information
        from the HTTP_ACCEPT_CHARSET header.
    """

    implements(IUnicodeEncodingConflictResolver)

    def resolve(self, context, text, expression):

        request = context.REQUEST

        charsets = getattr(request, '__zpt_available_charsets', None)
        if charsets is None:
            charsets = IUserPreferredCharsets(request).getPreferredCharsets()

            # add management_page_charset as one fallback
            management_charset = getattr(context, 'management_page_charset', None)
            if management_charset:
                charsets.append(management_charset)

            # add Python's default encoding as last fallback
            charsets.append(default_encoding)               

            # cache list of charsets
            request.__zpt_available_charsets = charsets

        for enc in charsets:
            if enc == '*': continue

            try:
                return unicode(text, enc)
            except (LookupError, UnicodeDecodeError):
                pass

        return text


StrictUnicodeEncodingConflictResolver = Z2UnicodeEncodingConflictResolver('strict')
ReplacingUnicodeEncodingConflictResolver = Z2UnicodeEncodingConflictResolver('replace')
IgnoringUnicodeEncodingConflictResolver = Z2UnicodeEncodingConflictResolver('ignore')
PreferredCharsetResolver = PreferredCharsetResolver()
