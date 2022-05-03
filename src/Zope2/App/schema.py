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

from zope.component import getUtility
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.interfaces import IVocabularyRegistry
from zope.schema.vocabulary import setVocabularyRegistry


@implementer(IVocabularyRegistry)
class Zope2VocabularyRegistry:
    """IVocabularyRegistry that supports global and local utilities.
    """
    __slots__ = ()

    def get(self, context, name):
        """See zope.schema.interfaces.IVocabularyRegistry.
        """
        factory = getUtility(IVocabularyFactory, name)
        return factory(context)


def configure_vocabulary_registry():
    setVocabularyRegistry(Zope2VocabularyRegistry())
