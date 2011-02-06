from zope.interface import Interface, implements
from OFS.SimpleItem import SimpleItem


class IDemoContent(Interface):

    def mymethod():
        """Return some text.
        """


class DemoContent(SimpleItem):

    implements(IDemoContent)

    def __init__(self, id, title):
        self.id = id
        self.title = title

    def mymethod(self):
        return "Hello world"
