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
            encoding = getattr(context, 'managment_page_charset', default_encoding)
            return unicode(text, encoding, self.mode)


StrictUnicodeEncodingConflictResolver = Z2UnicodeEncodingConflictResolver('strict')
ReplacingUnicodeEncodingConflictResolver = Z2UnicodeEncodingConflictResolver('replace')
IgnoringUnicodeEncodingConflictResolver = Z2UnicodeEncodingConflictResolver('ignore')
