##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Mimick Zope3 i18n machinery for Zope 2

$Id$
"""
from Acquisition import aq_get
from zope.i18n.interfaces import IFallbackTranslationDomainFactory
from zope.i18n.interfaces import ITranslationDomain
from zope.component import queryUtility
from zope.i18nmessageid import Message
from zope.publisher.interfaces.browser import IBrowserRequest


class FiveTranslationService:
    """Translation service that delegates to ``zope.i18n`` machinery.
    """
    # this is mostly a copy of zope.i18n.translate, with modifications
    # regarding fallback and Zope 2 compatability
    def translate(self, domain, msgid, mapping=None,
                  context=None, target_language=None, default=None):
        if isinstance(msgid, Message):
            domain = msgid.domain
            default = msgid.default
            mapping = msgid.mapping

        if default is None:
            default = unicode(msgid)

        if domain:
            util = queryUtility(ITranslationDomain, domain)
            if util is None:
                util = queryUtility(IFallbackTranslationDomainFactory)
                if util is not None:
                    util = util(domain)
        else:
            util = queryUtility(IFallbackTranslationDomainFactory)
            if util is not None:
                util = util()

        if util is None:
            # fallback to translation service that was registered,
            # DummyTranslationService the worst
            ts = _fallback_translation_service
            return ts.translate(domain, msgid, mapping=mapping, context=context,
                                target_language=target_language, default=default)

        # in Zope3, context is adapted to IUserPreferredLanguages,
        # which means context should be the request in this case.
        # Do not attempt to acquire REQUEST from the context, when we already
        # got a request as the context
        if context is not None:
            if not IBrowserRequest.providedBy(context):
                context = aq_get(context, 'REQUEST', None)
        return util.translate(msgid, mapping=mapping, context=context,
                              target_language=target_language, default=default)

# Hook that will be used by Products.PageTemplates.GlobalTranslationService
_fallback_translation_service = None
