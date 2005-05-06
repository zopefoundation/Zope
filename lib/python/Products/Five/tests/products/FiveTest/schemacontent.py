from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass

from zope.interface import implements
from interfaces import IComplexSchemaContent
from simplecontent import FieldSimpleContent

class ComplexSchemaContent(SimpleItem):
     implements(IComplexSchemaContent)

     meta_type ="Complex Schema Content"

     def __init__(self, id):
         self.id = id
         self.fish = FieldSimpleContent('fish', 'title')
         self.fish.description = ""
         self.fishtype = 'Lost fishy'

InitializeClass(ComplexSchemaContent)

def manage_addComplexSchemaContent(self, id, REQUEST=None):
    """Add the fancy fancy content."""
    id = self._setObject(id, ComplexSchemaContent(id))
    return ''
