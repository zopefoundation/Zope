##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Global Translation Service for providing I18n to Page Templates.

$Id: GlobalTranslationService.py,v 1.3 2002/10/06 17:21:07 efge Exp $
"""

class DummyTranslationService:
    """Translation service that doesn't know anything about translation."""
    def translate(self, domain, msgid, mapping=None,
                  context=None, target_language=None):
        return None
    # XXX Not all of Zope.I18n.ITranslationService is implemented.

translationService = DummyTranslationService()

def setGlobalTranslationService(service):
    """Sets the global translation service, and returns the previous one."""
    global translationService
    old_service = translationService
    translationService = service
    return old_service

def getGlobalTranslationService():
    """Returns the global translation service."""
    return translationService
