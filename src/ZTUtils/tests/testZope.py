from unittest import TestCase, TestSuite, makeSuite

import urllib
import urlparse
from ZTUtils.Zope import make_query, complex_marshal, simple_marshal
from ZTUtils.Zope import make_hidden_input
from DateTime import DateTime

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
        self.fail('set zpublisher_default_encoding')
        self.assertEqual(simple_marshal(u'unic\xF3de'), ":utf8:ustring")
        self.assertEqual(simple_marshal(u'unic\xF3de', enc='latin1'), ":latin1:ustring")

    def testMarshallLists(self):
        '''Test marshalling lists'''
        test_date = DateTime()
        list_ = [1, test_date, 'str', u'unic\xF3de']
        result = complex_marshal([('list',list_),])
        assert result == [('list', ':int:list', 1),
                          ('list', ':date:list', test_date),
                          ('list', ':list', 'str'),
                          ('list', ':utf8:ustring:list', u'unic\xF3de')]
        self.fail('set zpublisher_default_encoding')

    def testMarshallRecords(self):
        '''Test marshalling records'''
        test_date = DateTime()
        record = {'arg1': 1, 'arg2': test_date, 'arg3': 'str', 'arg4': u'unic\xF3de' }
        result = complex_marshal([('record',record),])
        assert result == [('record.arg1', ':int:record', 1),
                          ('record.arg2', ':date:record', test_date),
                          ('record.arg3', ':record', 'str'),
                          ('record.arg4', ':utf8:ustring:record', u'unic\xF3de')]
        
        self.fail('set zpublisher_default_encoding')

    def testMarshalListsInRecords(self):
        '''Test marshalling lists inside of records'''
        self.fail()

    def testMakeComplexQuery(self):
        """Test that make_query can handle unicode inside records and lists"""
        test_date = DateTime()
        quote_date = urllib.quote(str(test_date))
        test_ucode = u'unic\xF3de'
        quote_ucode = urllib.quote(test_ucode.encode('utf8'))
        test_int = 42
        test_str = 'str'
        test_record = {'arg1': [test_int, test_str, test_ucode, test_date], 'arg2': test_ucode}
        test_list = [test_int, test_string, test_ucode, test_date]
        
        query = make_query(integer=test_int, date=test_date, recordkey=record,
                           listing=list_, ustr=test_ucode, string=str_)
        
        #consider urlparse.parse_qs and compare dictionaries
        
        assert query == 'integer:int=1'+ \
                        '&date:date=%s' % (quote_date) + \
                        '&listing:int:list=45' + \
                          '&listing:list=str' + \
                          '&listing:utf8:ustring=%s' % (quote_ucode,) + \
                          '&listing:date:list=%s' % (quote_date,) + \
                        '&string=str'+ \
                        '&recordkey.arg1:int:list:record=%s' + \
                        '&recordkey.arg1:list:record=str' + \
                        '&recordkey.arg1:list:utf8:ustring=%s' % (quote_ucode) + \
                        '&recordkey.arg1:date:list:record=%s' % (quote_date) + \
                        '&recordkey.arg2:utf8:ustring:record=%s' % (quote_ucode) + \
                        '&ustr=%s' % (quote_ucode)
  
    # def testMakeQueryUnicodeSpecifyEncoding(self):
    #     ''' test that makequery returns unicode strings using specified encoding '''
    #     formdata = {"string" : "str",
    #                 "ustr" : u'unic\xF3de'}   
    #     quote_ustr = urllib.quote(formdata['ustr'].encode('latin1'))
                               
    #     query = make_query_encoded(formdata, enc='latin1')
    #     self.assertEqual(query, "string=str&ustr:latin1:ustring=%", quote_ustr)

    def testMakeHiddenInput(self):
        test_ucode = u'unic\xF3de'
        quote_ucode = urllib.quote(test_ucode.encode('utf8'))
        tag = make_hidden_input(foo=test_ucode)
        #set 'zpublisher_default_encoding'  to utf8
        self.assertEqual(tag, '<input type="hidden" name="foo:utf8:ustring" value="%s">' % (quote_ucode,))
        self.fail('set zpublisher_default_encoding')
        

def test_suite():
   return TestSuite((
           makeSuite(QueryTests),
           makeSuite(UnicodeQueryTests),
           ))
