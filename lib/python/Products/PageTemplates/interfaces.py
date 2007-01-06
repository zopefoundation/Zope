

from zope.interface import Interface

class IUnicodeEncodingConflictResolver(Interface):

    def resolve(context, text):
        """ Returns 'text' as unicode string. 
            'context' is the current context object
        """


