###########################################################################
# TextIndexNG V 3                
# The next generation TextIndex for Zope
#
# This software is governed by a license. See
# LICENSE.txt for the terms of this license.
###########################################################################



from zope.component.interfaces import IFactory
from zope.interface import implements, implementedBy

from Products.PageTemplates.interfaces import IUnicodeEncodingConflictResolver

class UnicodeEncodingResolver:

    implements(IUnicodeEncodingConflictResolver)

    def __init__(self, context, text):
        self.context = context
        self.text = text

    def resolve(self, context, text):
        return unicode(self.text, errors='replace')

class UnicodeEncodingResolverFactory:
    
    implements(IFactory)

    def __call__(self, context, text):
        return UnicodeEncodingResolver(context, text)

    def getInterfaces(self):
        return implementedBy(UnicodeEncodingResolverFactory)

UnicodeEncodingResolverFactory = UnicodeEncodingResolverFactory() 
