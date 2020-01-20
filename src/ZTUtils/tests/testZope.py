import unittest
from urllib.parse import quote

from DateTime import DateTime
from ZTUtils.Zope import complex_marshal
from ZTUtils.Zope import make_hidden_input
from ZTUtils.Zope import make_query
from ZTUtils.Zope import simple_marshal


class QueryTests(unittest.TestCase):

    def testMarshalString(self):
        self.assertEqual(simple_marshal('string'), '')

    def testMarshalBool(self):
        self.assertEqual(simple_marshal(True), ':boolean')

    def testMarshalInt(self):
        self.assertEqual(simple_marshal(42), ":int")

    def testMarshalFloat(self):
        self.assertEqual(simple_marshal(3.1415), ":float")

    def testMarshalDate(self):
        self.assertEqual(simple_marshal(DateTime()), ":date")

    def testMarshalUnicode(self):
        arg_type = ''
        self.assertEqual(simple_marshal('unic\xF3de'), arg_type)

    def testMarshallLists(self):
        '''Test marshalling lists'''
        test_date = DateTime()
        list_ = [1, test_date, 'str', 'unic\xF3de']
        result = complex_marshal([('list', list_), ])
        arg4_type = ':list'
        self.assertEqual(result,
                         [('list', ':int:list', 1),
                          ('list', ':date:list', test_date),
                          ('list', ':list', 'str'),
                          ('list', arg4_type, 'unic\xF3de')])

    def testMarshallRecords(self):
        '''Test marshalling records'''
        test_date = DateTime()
        record = {
            'arg1': 1, 'arg2': test_date,
            'arg3': 'str', 'arg4': 'unic\xF3de',
        }
        result = complex_marshal([('record', record), ])
        arg4_type = ':record'
        self.assertEqual(
            set(result),
            {('record.arg1', ':int:record', 1),
             ('record.arg2', ':date:record', test_date),
             ('record.arg3', ':record', 'str'),
             ('record.arg4', arg4_type, 'unic\xF3de')})

    def testMarshallListsInRecords(self):
        '''Test marshalling lists inside of records'''
        test_date = DateTime()
        record = {'arg1': [1, test_date, 'str', 'unic\xF3de'], 'arg2': 1}
        result = complex_marshal([('record', record), ])
        arg1_type = ':list:record'
        self.assertEqual(
            set(result),
            {('record.arg1', ':int:list:record', 1),
             ('record.arg1', ':date:list:record', test_date),
             ('record.arg1', ':list:record', 'str'),
             ('record.arg1', arg1_type, 'unic\xF3de'),
             ('record.arg2', ':int:record', 1)})

    def testMakeComplexQuery(self):
        '''Test that make_query returns sane results'''
        test_date = DateTime()
        quote_date = quote(str(test_date))
        record = {'arg1': [1, test_date, 'str'], 'arg2': 1}
        list_ = [1, test_date, 'str']
        int_ = 1
        str_ = 'str'
        query = make_query(date=test_date, integer=int_, listing=list_,
                           record=record, string=str_)

        self.assertEqual(
            set(query.split('&')),
            {
                'date:date=%s' % quote_date,
                'integer:int=1',
                'listing:int:list=1',
                'listing:date:list=%s' % quote_date,
                'listing:list=str',
                'string=str',
                'record.arg1:int:list:record=1',
                'record.arg1:date:list:record=%s' % quote_date,
                'record.arg1:list:record=str',
                'record.arg2:int:record=1',
            })

    def testMakeQueryUnicode(self):
        ''' Test makequery against Github issue 15
           https://github.com/zopefoundation/Zope/issues/15
        '''
        query = make_query(search_text='unic\xF3de')
        arg_type = 'search_text='
        self.assertEqual(arg_type + 'unic%C3%B3de', query)

    def testMakeHiddenInput(self):
        tag = make_hidden_input(foo='bar')
        self.assertEqual(tag, '<input type="hidden" name="foo" value="bar">')
        tag = make_hidden_input(foo=1)
        self.assertEqual(tag, '<input type="hidden" name="foo:int" value="1">')
        # Escaping
        tag = make_hidden_input(foo='bar & baz')
        self.assertEqual(
            tag, '<input type="hidden" name="foo" value="bar &amp; baz">')
        tag = make_hidden_input(foo='<bar>')
        self.assertEqual(
            tag, '<input type="hidden" name="foo" value="&lt;bar&gt;">')
        tag = make_hidden_input(foo='"bar"')
        self.assertEqual(
            tag, '<input type="hidden" name="foo" value="&quot;bar&quot;">')
