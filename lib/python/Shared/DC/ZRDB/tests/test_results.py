""" Unit tests for Products.RHGDelivery.simpleresults

$Id: test_results.py,v 1.2 2005/09/07 21:25:47 tseaver Exp $
"""
import unittest

from ExtensionClass import Base
from Acquisition import aq_parent

class Brain:
    def __init__(self, *args): pass

Parent = Base()

class TestResults(unittest.TestCase):

    # test fixtures
    columns = [ {'name' : 'string', 'type' : 't', 'width':1},
                {'name':'int', 'type': 'i'} ]
    data = [['string1', 1], ['string2', 2]]

    def _getTargetClass(self):
        from Shared.DC.ZRDB.Results import Results
        return Results
    
    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_searchable_result_columns(self):
        ob = self._makeOne((self.columns, self.data))
        self.assertEqual(ob._searchable_result_columns(), self.columns)

    def test_names(self):
        ob = self._makeOne((self.columns, self.data))
        self.assertEqual(ob.names(), ['string', 'int'])

    def test_data_dictionary(self):
        ob = self._makeOne((self.columns, self.data))
        self.assertEqual(
            ob.data_dictionary(),
            { 'string':{'name' : 'string', 'type' : 't', 'width':1},
              'int':{'name':'int', 'type': 'i'} }
            )

    def test_len(self):
        ob = self._makeOne((self.columns, self.data))
        self.assertEqual(len(ob), 2)

    def test_getitem(self):
        ob = self._makeOne((self.columns, self.data))
        row = ob[0]
        self.assertEquals(row[0], 'string1')
        self.assertEquals(row[1], 1)
        row = ob[1]
        self.assertEquals(row[0], 'string2')
        self.assertEquals(row[1], 2)

    def test_getattr_and_aliases(self):
        ob = self._makeOne((self.columns, self.data))
        row = ob[0]
        self.assertEqual(row.string, 'string1')
        self.assertEqual(row.int, 1)
        self.assertEqual(row.STRING, 'string1')
        self.assertEqual(row.INT, 1)
        row = ob[1]
        self.assertEqual(row.string, 'string2')
        self.assertEqual(row.int, 2)
        self.assertEqual(row.STRING, 'string2')
        self.assertEqual(row.INT, 2)

    def test_suppliedbrain(self):
        ob = self._makeOne((self.columns, self.data), brains=Brain)
        row = ob[0]
        self.failUnless(isinstance(row, Brain))

    def test_suppliedparent(self):
        ob = self._makeOne((self.columns, self.data), parent=Parent)
        row = ob[0]
        self.failUnless(aq_parent(row) is Parent)

    def test_tuples(self):
        ob = self._makeOne((self.columns, self.data))
        tuples = ob.tuples()
        self.assertEqual( tuples, [('string1', 1), ('string2', 2)] )

    def test_dictionaries(self):
        ob = self._makeOne((self.columns, self.data))
        dicts = ob.dictionaries()
        self.assertEqual( dicts, [{'string':'string1', 'int':1},
                                  {'string':'string2', 'int':2}] )

    def test_asRDB(self):
        ob = self._makeOne((self.columns, self.data))
        asrdb = ob.asRDB()
        columns = ['string\tint', '1t\ti', 'string1\t1', 'string2\t2\n']
        self.assertEqual(asrdb, '\n'.join(columns))

    def _set_noschema(self, row):
        row.cantdoit = 1

    def test_recordschema(self):
        ob = self._makeOne((self.columns, self.data))
        row = ob[0]
        self.assertEqual(row.__record_schema__, {'string':0, 'int':1})
        self.assertRaises(AttributeError, self._set_noschema, row)

    def test_record_as_read_mapping(self):
        ob = self._makeOne((self.columns, self.data))
        row = ob[0]
        self.assertEqual('%(string)s %(int)s' % row, 'string1 1')
        row = ob[1]
        self.assertEqual('%(string)s %(int)s' % row, 'string2 2')

    def test_record_as_write_mapping(self):
        ob = self._makeOne((self.columns, self.data))
        row = ob[0]
        row['int'] = 5
        self.assertEqual('%(string)s %(int)s' % row, 'string1 5')

    def test_record_as_write_mapping2(self):
        ob = self._makeOne((self.columns, self.data))
        row = ob[0]
        row.int = 5
        self.assertEqual('%(string)s %(int)s' % row, 'string1 5')

    def test_record_as_sequence(self):
        ob = self._makeOne((self.columns, self.data))
        row = ob[0]
        self.assertEqual(row[0], 'string1')
        self.assertEqual(row[1], 1)
        self.assertEqual(list(row), ['string1', 1])
        row = ob[1]
        self.assertEqual(row[0], 'string2')
        self.assertEqual(row[1], 2)
        self.assertEqual(list(row), ['string2', 2])

    def test_record_of(self):
        ob = self._makeOne((self.columns, self.data))
        row = ob[0]
        wrapped = row.__of__(Parent)
        self.assertEqual(wrapped.aq_self, row)
        self.assertEqual(wrapped.aq_parent, Parent)

    def test_record_hash(self):
        ob = self._makeOne((self.columns, self.data))
        row = ob[0]
        self.assert_(isinstance(hash(row), int))

    def test_record_len(self):
        ob = self._makeOne((self.columns, self.data))
        row = ob[0]
        self.assertEqual(len(row), 2)

    def _add(self, row1, row2):
        return row1 + row2

    def test_record_add(self):
        ob = self._makeOne((self.columns, self.data))
        row1 = ob[0]
        row2 = ob[1]
        self.assertRaises(TypeError, self._add, row1, row2)

    def _slice(self, row):
        return row[1:]

    def test_record_slice(self):
        ob = self._makeOne((self.columns, self.data))
        row = ob[0]
        self.assertRaises(TypeError, self._slice, row)

    def _mul(self, row):
        return row * 3

    def test_record_mul(self):
        ob = self._makeOne((self.columns, self.data))
        row = ob[0]
        self.assertRaises(TypeError, self._mul, row)

    def _del(self, row):
        del row[0]

    def test_record_delitem(self):
        ob = self._makeOne((self.columns, self.data))
        row = ob[0]
        self.assertRaises(TypeError, self._del, row)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestResults))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
