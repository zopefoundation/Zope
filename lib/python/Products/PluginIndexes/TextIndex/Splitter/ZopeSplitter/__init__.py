from Splitter import Splitter

class ZopeSplitter:

    meta_type="Splitter"
    description="Zope Default Splitter"

    Splitter = Splitter

    def __init__(self):
        print "__init__"

    def a(self):
        """a"""
        print "initialize",self.meta_type
        pass

    def b(self):
        """b"""

        print "binitialize",self.meta_type
        pass

