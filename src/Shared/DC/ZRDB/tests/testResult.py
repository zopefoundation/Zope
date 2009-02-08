from unittest import TestCase, TestSuite, makeSuite, main
from cStringIO import StringIO
from ExtensionClass import Base
from Shared.DC.ZRDB.Results import Results
from Shared.DC.ZRDB import RDB

class Brain:
    def __init__(self, *args): pass

Parent = Base()

class TestResults(TestCase):

    def test_results(self):
        r = Results(([{'name':'foo', 'type':'integer'},
                      {'name':'bar', 'type':'integer'}],
                     ((1, 2), (3, 4))),
                    brains=Brain,
                    parent=Parent)
        self.assertEquals(len(r), 2)
        row = r[0]
        self.assertEquals(row[0], 1)
        self.assertEquals(row[1], 2)
        self.assertEquals(row.foo, 1)
        self.assertEquals(row.bar, 2)
        self.assertEquals(row.FOO, 1)
        self.assertEquals(row.BAR, 2)
        row = r[1]
        self.assertEquals(row[0], 3)
        self.assertEquals(row[1], 4)
        self.assertEquals(row.foo, 3)
        self.assertEquals(row.bar, 4)
        self.assertEquals(row.FOO, 3)
        self.assertEquals(row.BAR, 4)
        self.failUnless(isinstance(row, Brain))

    def test_rdb_file(self):
        infile = StringIO("""\
        foo\tbar
        2i\t2i
        1\t2
        3\t4\
        """)
        r = RDB.File(infile,
                     brains=Brain,
                     parent=Parent)
        self.assertEquals(len(r), 2)
        row = r[0]
        self.assertEquals(row[0], 1)
        self.assertEquals(row[1], 2)
        self.assertEquals(row.foo, 1)
        self.assertEquals(row.bar, 2)
        self.assertEquals(row.FOO, 1)
        self.assertEquals(row.BAR, 2)
        row = r[1]
        self.assertEquals(row[0], 3)
        self.assertEquals(row[1], 4)
        self.assertEquals(row.foo, 3)
        self.assertEquals(row.bar, 4)
        self.assertEquals(row.FOO, 3)
        self.assertEquals(row.BAR, 4)
        self.failUnless(isinstance(row, Brain))

def test_suite():
    return TestSuite((makeSuite(TestResults),))

if __name__ == '__main__':
    main(defaultTest='test_suite')
