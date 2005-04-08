from Testing import ZopeTestCase
from Products.PluginIndexes.PathIndex.PathIndex import PathIndex


class Dummy:

    meta_type="foo"

    def __init__(self, path):
        self.path = path

    def getPhysicalPath(self):
        return self.path.split('/')

    def __str__(self):
        return '<Dummy: %s>' % self.path

    __repr__ = __str__


class PathIndexTestCase(ZopeTestCase.ZopeTestCase):

    def _setup(self):
        self._index = PathIndex( 'path' )
        self._values = {
          1 : Dummy("/aa/aa/aa/1.html"),
          2 : Dummy("/aa/aa/bb/2.html"),
          3 : Dummy("/aa/aa/cc/3.html"),
          4 : Dummy("/aa/bb/aa/4.html"),
          5 : Dummy("/aa/bb/bb/5.html"),
          6 : Dummy("/aa/bb/cc/6.html"),
          7 : Dummy("/aa/cc/aa/7.html"),
          8 : Dummy("/aa/cc/bb/8.html"),
          9 : Dummy("/aa/cc/cc/9.html"),
          10 : Dummy("/bb/aa/aa/10.html"),
          11 : Dummy("/bb/aa/bb/11.html"),
          12 : Dummy("/bb/aa/cc/12.html"),
          13 : Dummy("/bb/bb/aa/13.html"),
          14 : Dummy("/bb/bb/bb/14.html"),
          15 : Dummy("/bb/bb/cc/15.html"),
          16 : Dummy("/bb/cc/aa/16.html"),
          17 : Dummy("/bb/cc/bb/17.html"),
          18 : Dummy("/bb/cc/cc/18.html")
        }

    def _populateIndex(self):
        for k, v in self._values.items():
            self._index.index_object( k, v )


class ExtendedPathIndexTestCase(PathIndexTestCase):

    def _setup(self):
        self._index = PathIndex( 'path' )
        self._values = {
          1 : Dummy("/1.html"),
          2 : Dummy("/aa/2.html"),
          3 : Dummy("/aa/aa/3.html"),
          4 : Dummy("/aa/aa/aa/4.html"),
          5 : Dummy("/aa/bb/5.html"),
          6 : Dummy("/aa/bb/aa/6.html"),
          7 : Dummy("/aa/bb/bb/7.html"),
          8 : Dummy("/aa"),
          9 : Dummy("/aa/bb"),
          10 : Dummy("/bb/10.html"),
          11 : Dummy("/bb/bb/11.html"),
          12 : Dummy("/bb/bb/bb/12.html"),
          13 : Dummy("/bb/aa/13.html"),
          14 : Dummy("/bb/aa/aa/14.html"),
          15 : Dummy("/bb/bb/aa/15.html"),
          16 : Dummy("/bb"),
          17 : Dummy("/bb/bb"),
          18 : Dummy("/bb/aa")
        }

