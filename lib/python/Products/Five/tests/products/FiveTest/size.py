from zope.interface import implements
from zope.app.size.interfaces import ISized

class SimpleContentSize(object):
    """Size for ``SimpleContent`` objects."""
    implements(ISized)

    def __init__(self, context):
	self.context = context

    def sizeForSorting(self):
	return ('byte', 42)

    def sizeForDisplay(self):
	return "What is the meaning of life?"

class FancyContentSize(object):
    """Size for ``SimpleContent`` objects."""
    implements(ISized)

    def __init__(self, context):
	self.context = context

    def sizeForSorting(self):
	return ('line', 143)

    def sizeForDisplay(self):
	return "That's not the meaning of life!"
