from unittest import TestCase, TestSuite, makeSuite

import urllib
import urlparse
from ZTUtils.Zope import make_query, complex_marshal, simple_marshal
from ZTUtils.Zope import make_hidden_input
from DateTime import DateTime

#mock ZTUtils.Zope._default_encoding to avoid config setup
def _default_encoding(): 
    return 'utf8'
import ZTUtils.Zope
ZTUtils.Zope._default_encoding = _default_encoding


class QueryTests(TestCase):

    def testSimpleMarshal(self):
        '''Simple Marshal Complete Test'''
        self.assertEqual(simple_marshal('string'), '')
        self.assertEqual(simple_marshal(True), ':boolean')
        self.assertEqual(simple_marshal(42), ":int")
        self.assertEqual(simple_marshal(3.1415), ":float")
        self.assertEqual(simple_marshal(DateTime()), ":date")
        
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

    def testMarshallRecordsInLists(self):
        '''Test marshalling records inside lists'''
        test_date = DateTime()
        record = {'arg1': [1, test_date, 'str'], 'arg2': 1}
        test_list = ['top', record, 12]
        result = complex_marshal([('list_key',test_list),])
        self.maxDiff = 1000
        self.assertEqual(result,
                         [('list_key', ':list', 'top'),
                          ('list_key.arg1', ':int:list:record:list', 1),
                          ('list_key.arg1', ':date:list:record:list', test_date),
                          ('list_key.arg1', ':list:record:list', 'str'),
                          ('list_key.arg2', ':int:record:list', 1),
                          ('list_key', ':int:list', 12)]
                         )

    def testMarshallRecordsInRecords(self):
        '''Test marshalling records inside records'''
        sub_record = {'sub1': 'deep', 'sub2': 1}
        record = {'arg1':'top', 'arg2':sub_record, 'arg3':12}
        result = complex_marshal([('r_record',record),])
        self.maxDiff = 1000

        #dictionaries dont' preserve order - use self.assertItemsEqual
        self.assertItemsEqual(result,
                              [('r_record.arg1', ':record', 'top'),
                               ('r_record.arg2.sub1', ':record:record', 'deep'),
                               ('r_record.arg2.sub2', ':int:record:record', 1),
                               ('r_record.arg3', ':int:record', 12)]
                              )

    def testMarshallListsInLists(self):
        '''Test marshalling lists in lists'''
        #As you see, you cannot see the boundry between sub_list1 and sub_list2
        #this is an 'oops'. There is no way to marshal this back into a list of lists
        #Solution: Use a delimiter :)
        test_date = DateTime()
        sub_list = [1, test_date, 'str']
        sub_list2 = [42, test_date, '2ndstr']
        list_ = [sub_list,"delimiter ha!", sub_list2]
        result = complex_marshal([('lil',list_),])
        self.assertEqual(result,
                         [('lil', ':int:list:list', 1),
                          ('lil', ':date:list:list', test_date),
                          ('lil', ':list:list', 'str'),
                          ('lil', ':list', 'delimiter ha!'),
                          ('lil', ':int:list:list', 42),
                          ('lil', ':date:list:list', test_date),
                          ('lil', ':list:list', '2ndstr')])

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
        
        #XXX This test relies on dictionary ordering, which is unpredictable.
        ### consider urlparse.parse_qs and compare dictionaries
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
            
        
class UnicodeQueryTests(TestCase):
    """Duplicating all tests under 'QueryTests' and include unicode handling"""

    def testSimpleMarshal(self):
        self.assertEqual(simple_marshal(u'unic\xF3de'), ":utf8:ustring")

    def testMarshallLists(self):
        '''Test marshalling lists'''
        test_date = DateTime()
        test_unicode =  u'unic\xF3de'
        list_ = [1, test_date, 'str', test_unicode]
        result = complex_marshal([('list',list_),])
        assert result == [('list', ':int:list', 1),
                          ('list', ':date:list', test_date),
                          ('list', ':list', 'str'),
                          ('list', ':utf8:ustring:list', test_unicode.encode('utf8'))]

    def testMarshallRecords(self):
        '''Test marshalling records'''
        test_date = DateTime()
        test_unicode =  u'unic\xF3de'
        record = {'arg1': 1, 'arg2': test_date, 'arg3': 'str', 'arg4': test_unicode }
        result = complex_marshal([('record',record),])
        assert result == [('record.arg1', ':int:record', 1),
                          ('record.arg2', ':date:record', test_date),
                          ('record.arg3', ':record', 'str'),
                          ('record.arg4', ':utf8:ustring:record', test_unicode.encode('utf8'))]

    def testMarshalListsInRecords(self):
        '''Test marshalling lists inside of records'''
        test_date = DateTime()
        test_unicode =  u'unic\xF3de'
        record = {'arg1': [1, test_date, test_unicode], 'arg2': 1, 'arg3':  test_unicode}
        result = complex_marshal([('record',record),])

        expect = [('record.arg1', ':int:list:record', 1),
                  ('record.arg1', ':date:list:record', test_date),
                  ('record.arg1', ':utf8:ustring:list:record', test_unicode.encode('utf8')),
                  ('record.arg2', ':int:record', 1),
                  ('record.arg3', ':utf8:ustring:record', test_unicode.encode('utf8'))]

        self.assertEqual(result, expect)

    def testMakeQuery(self):
        test_str = 'foo'
        test_unicode = u'\u03dd\xf5\xf6'
        query = make_query(str_key=test_str, unicode_key=test_unicode)
        
        expect = {'str_key': test_str,
                  'unicode_key':  urllib.quote(test_unicode.encode('utf8'))
                  }

        result = parse_qs_nolist(query)
        
    def testMakeComplexQuery(self):
        """Test that make_query returns sane results"""
        test_date = DateTime()
        test_unicode = u'unic\xF3de'
        test_int = 42
        test_str = 'str'
        test_record = {'arg1': [test_int, test_str, test_unicode, test_date], 'arg2': test_unicode}
        test_list = [test_int, test_str, test_unicode, test_date]
        
        query = make_query(int_key=test_int, date_key=test_date,
                           str_key=test_str, unicode_key=test_unicode, 
                           record_key=test_record, list_key=test_list)
        
        expect = {'int_key:int': str(test_int),
                  'date_key:date':  str(test_date),
                  'str_key': test_str,
                  'unicode_key:utf8:ustring': test_unicode.encode('utf8'),
                  'record_key.arg1:int:list:record': str(test_int),
                  'record_key.arg1:list:record': test_str,
                  'record_key.arg1:utf8:ustring:list:record':test_unicode.encode('utf8'),
                  'record_key.arg1:date:list:record': str(test_date),
                  'record_key.arg2:utf8:ustring:record': test_unicode.encode('utf8'),
                  'list_key:int:list': str(test_int),
                  'list_key:list': test_str,
                  'list_key:utf8:ustring:list': test_unicode.encode('utf8'),
                  'list_key:date:list': str(test_date)
                  }

        result = parse_qs_nolist(query)
        
        self.maxDiff=3000
        self.assertEqual(expect, result)

    def testMakeHiddenInput(self):
        test_unicode = u'unic\xF3de'
        quote_unicode = test_unicode.encode('utf8')
        tag = make_hidden_input(foo=test_unicode)
        #set 'zpublisher_default_encoding'  to utf8
        self.assertEqual(tag, '<input type="hidden" name="foo:utf8:ustring" value="%s">' % (quote_unicode,))


class ComplexMarshalRecursionTests(TestCase):
    """Test using ComplexMarshal badly..."""

    def testRecursionError(self):
        list_=['a','b','c']
        list_.append(list_)
        self.assertRaises(RuntimeError, complex_marshal, [('this_is_bad', list_)])

class UnicodeEncodingTests(TestCase):
    """ test behavior if encoding is specified """
    # def testMakeQueryUnicodeSpecifyEncoding(self):
    #     ''' test that makequery returns unicode strings using specified encoding '''
    #     formdata = {"string" : "str",
    #                 "ustr" : u'unic\xF3de'}   
    #     quote_ustr = urllib.quote(formdata['ustr'].encode('latin1'))
                               
    #     query = make_query_encoded(formdata, enc='latin1')
    #     self.assertEqual(query, "string=str&ustr:latin1:ustring=%", quote_ustr)
    pass

def parse_qs_nolist(qs):
    '''turn list values retuned from urlparse.parse_qs into scalars'''
    d = urlparse.parse_qs(qs)
    for k in d:
        d[k] = d[k][0]
    return d

def test_suite():
   return TestSuite((
           makeSuite(QueryTests),
           makeSuite(UnicodeQueryTests),
           makeSuite(UnicodeEncodingTests),
           makeSuite(ComplexMarshalRecursionTests),
           ))


