from zope.interface import Interface, implements

from Products.Five import BrowserView
from AccessControl import ClassSecurityInfo

class IDummy(Interface):
    """Just a marker interface"""

class DummyView(BrowserView):
    """A dummy view"""

    def foo(self):
        """A foo"""
        return 'A foo view'

class Dummy1:
    implements(IDummy)
    def foo(self): pass
    def bar(self): pass
    def baz(self): pass
    def keg(self): pass
    def wot(self): pass

class Dummy2(Dummy1):
    security = ClassSecurityInfo()
    security.declarePublic('foo')
    security.declareProtected('View management screens', 'bar')
    security.declarePrivate('baz')
    security.declareProtected('View management screens', 'keg')
