import os, sys

from unittest import TestCase, makeSuite, main

import string
import urllib
from ZTUtils.Zope import make_query, complex_marshal
from ZTUtils.Zope import make_hidden_input
from DateTime import DateTime

class QueryTests(TestCase):

    def testMarshallLists(self):
        '''Test marshalling lists'''
        test_date = DateTime()
        list_ = [1, test_date, 'str']
        result = complex_marshal([('list',list_),])
        assert result == [('list', ':int:list', 1),
                          ('list', ':date:list', test_date),
                          ('list', ':list', 'str')]

    def testMarshallRecords(self):
        '''Test marshalling records'''
        test_date = DateTime()
        record = {'arg1': 1, 'arg2': test_date, 'arg3': 'str'}
        result = complex_marshal([('record',record),])
        assert result == [('record.arg1', ':int:record', 1),
                          ('record.arg2', ':date:record', test_date),
                          ('record.arg3', ':record', 'str')]

    def testMarshallListsInRecords(self):
        '''Test marshalling lists inside of records'''
        test_date = DateTime()
        record = {'arg1': [1, test_date, 'str'], 'arg2': 1}
        result = complex_marshal([('record',record),])
        assert result == [('record.arg1', ':int:list:record', 1),
                          ('record.arg1', ':date:list:record', test_date),
                          ('record.arg1', ':list:record', 'str'),
                          ('record.arg2', ':int:record', 1)]

    def testMakeComplexQuery(self):
        '''Test that make_query returns sane results'''
        test_date = DateTime()
        quote_date = urllib.quote(str(test_date))
        record = {'arg1': [1, test_date, 'str'], 'arg2': 1}
        list_ = [1, test_date, 'str']
        date = test_date
        int_ = 1
        str_ = 'str'
        query = make_query(date=test_date, integer=int_, listing=list_,
                           record=record, string=str_)
        assert query == 'date:date=%s&integer:int=1&listing:int:list=1&listing:date:list=%s&listing:list=str&string=str&record.arg1:int:list:record=1&record.arg1:date:list:record=%s&record.arg1:list:record=str&record.arg2:int:record=1'%(quote_date,quote_date,quote_date)

    def testMakeHiddenInput(self):
        tag = make_hidden_input(foo='bar')
        self.assertEqual(tag, '<input type="hidden" name="foo" value="bar">')
        tag = make_hidden_input(foo=1)
        self.assertEqual(tag, '<input type="hidden" name="foo:int" value="1">')
        # Escaping
        tag = make_hidden_input(foo='bar & baz')
        self.assertEqual(tag, '<input type="hidden" name="foo" value="bar &amp; baz">')
        tag = make_hidden_input(foo='<bar>')
        self.assertEqual(tag, '<input type="hidden" name="foo" value="&lt;bar&gt;">')
        tag = make_hidden_input(foo='"bar"')
        self.assertEqual(tag, '<input type="hidden" name="foo" value="&quot;bar&quot;">')

def test_suite():
    return makeSuite(QueryTests)

if __name__=='__main__':
    main()
