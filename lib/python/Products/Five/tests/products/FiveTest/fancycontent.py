import Acquisition
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass

from zope.interface import implements
from interfaces import IFancyContent

class FancyAttribute(Acquisition.Explicit):
    """Doc test fanatics"""

    def __init__(self, name):
        self.name = name

    security = ClassSecurityInfo()

    security.declarePublic('index_html')
    def index_html(self, REQUEST):
        """Doc test fanatics"""
        return self.name

InitializeClass(FancyAttribute)

class FancyContent(SimpleItem):
    """A class that already comes with its own __bobo_traverse__ handler.
    Quite fancy indeed."""
    implements(IFancyContent)

    meta_type = "Fancy Content"
    security = ClassSecurityInfo()

    def __bobo_traverse__(self, REQUEST, name):
        return FancyAttribute(name).__of__(self)

InitializeClass(FancyContent)

def manage_addFancyContent(self, id, REQUEST=None):
    """Add the fancy fancy content."""
    id = self._setObject(id, FancyContent(id))
    return ''
