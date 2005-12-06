##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Global Translation Service for providing I18n to Page Templates.

$Id$
"""

import re
import Products.Five.i18n

from DocumentTemplate.DT_Util import ustr
from TAL.TALDefs import NAME_RE

class DummyTranslationService:
    """Translation service that doesn't know anything about translation."""
    def translate(self, domain, msgid, mapping=None,
                  context=None, target_language=None, default=None):
        def repl(m, mapping=mapping):
            return ustr(mapping[m.group(m.lastindex)])
        cre = re.compile(r'\$(?:(%s)|\{(%s)\})' % (NAME_RE, NAME_RE))
        return cre.sub(repl, default or msgid)
    # XXX Not all of Zope2.I18n.ITranslationService is implemented.

#
# As of Five 1.1, we're by default using Zope 3 Message Catalogs for
# translation, but we allow fallback translation services such as PTS
# and Localizer
#

Products.Five.i18n._fallback_translation_service = DummyTranslationService()
fiveTranslationService = Products.Five.i18n.FiveTranslationService()

def getGlobalTranslationService():
    return fiveTranslationService

def setGlobalTranslationService(newservice):
    oldservice, Products.Five.i18n._fallback_translation_service = \
        Products.Five.i18n._fallback_translation_service, newservice
    return oldservice
