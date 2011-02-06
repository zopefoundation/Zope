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
"""Five-specific schema support

$Id$
"""
from zope.component import getUtility
from zope.interface import implements
from zope.schema.interfaces import IVocabularyRegistry
from zope.schema.interfaces import IVocabularyFactory

class Zope2VocabularyRegistry(object):
    """IVocabularyRegistry that supports global and local utilities.

    Cloned from the version in zope.app.schema.vocabulary:  it was the
    only feature in that package!
    """
    implements(IVocabularyRegistry)
    __slots__ = ()

    def get(self, context, name):
        """See zope.schema.interfaces.IVocabularyRegistry.
        """
        factory = getUtility(IVocabularyFactory, name)
        return factory(context)
