import unittest
from urllib import quote_plus

class RecordTests( unittest.TestCase ):

    def test_repr( self ):
        from ZPublisher.HTTPRequest import record
        record = record()
        record.a = 1
        record.b = 'foo'
        r = repr( record )
        d = eval( r )
        self.assertEqual( d, record.__dict__ )


class ProcessInputsTests(unittest.TestCase):
    def _getHTTPRequest(self, env):
        from ZPublisher.HTTPRequest import HTTPRequest
        return HTTPRequest(None, env, None)

    def _processInputs(self, inputs):
        # Have the inputs processed, and return a HTTPRequest object holding the
        # result.
        # inputs is expected to be a list of (key, value) tuples, no CGI
        # encoding is required.

        query_string = []
        add = query_string.append
        for key, val in inputs:
            add("%s=%s" % (quote_plus(key), quote_plus(val)))
        query_string = '&'.join(query_string)
        
        env = {'SERVER_NAME': 'testingharnas', 'SERVER_PORT': '80'}
        env['QUERY_STRING'] = query_string
        req = self._getHTTPRequest(env)
        req.processInputs()
        return req

    def testNoMarshalling(self):
        inputs = (
            ('foo', 'bar'), ('spam', 'eggs'),
            ('number', '1'),
            ('spacey key', 'val'), ('key', 'spacey val'),
            ('multi', '1'), ('multi', '2'))
        req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEquals(formkeys, ['foo', 'key', 'multi', 'number',
            'spacey key', 'spam'])
        self.assertEquals(req['number'], '1')
        self.assertEquals(req['multi'], ['1', '2'])
        self.assertEquals(req['spacey key'], 'val')
        self.assertEquals(req['key'], 'spacey val')

    def testSimpleMarshalling(self):
        from DateTime import DateTime
    
        inputs = (
            ('num:int', '42'), ('fract:float', '4.2'), ('bign:long', '45'),
            ('words:string', 'Some words'), ('2tokens:tokens', 'one two'),
            ('aday:date', '2002/07/23'),
            ('accountedfor:required', 'yes'),
            ('multiline:lines', 'one\ntwo'),
            ('morewords:text', 'one\ntwo\n'))
        req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEquals(formkeys, ['2tokens', 'accountedfor', 'aday', 'bign',
            'fract', 'morewords', 'multiline', 'num', 'words'])

        self.assertEquals(req['2tokens'], ['one', 'two'])
        self.assertEquals(req['accountedfor'], 'yes')
        self.assertEquals(req['aday'], DateTime('2002/07/23'))
        self.assertEquals(req['bign'], 45L)
        self.assertEquals(req['fract'], 4.2)
        self.assertEquals(req['morewords'], 'one\ntwo\n')
        self.assertEquals(req['multiline'], ['one', 'two'])
        self.assertEquals(req['num'], 42)
        self.assertEquals(req['words'], 'Some words')

    def testSimpleContainers(self):
        inputs = (
            ('oneitem:list', 'one'),
            ('alist:list', 'one'), ('alist:list', 'two'),
            ('oneitemtuple:tuple', 'one'),
            ('atuple:tuple', 'one'), ('atuple:tuple', 'two'),
            ('onerec.foo:record', 'foo'), ('onerec.bar:record', 'bar'),
            ('setrec.foo:records', 'foo'), ('setrec.bar:records', 'bar'),
            ('setrec.foo:records', 'spam'), ('setrec.bar:records', 'eggs'))
        req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEquals(formkeys, ['alist', 'atuple', 'oneitem',
            'oneitemtuple', 'onerec', 'setrec'])
        
        self.assertEquals(req['oneitem'], ['one'])
        self.assertEquals(req['oneitemtuple'], ('one',))
        self.assertEquals(req['alist'], ['one', 'two'])
        self.assertEquals(req['atuple'], ('one', 'two'))
        self.assertEquals(req['onerec'].foo, 'foo')
        self.assertEquals(req['onerec'].bar, 'bar')
        self.assertEquals(len(req['setrec']), 2)
        self.assertEquals(req['setrec'][0].foo, 'foo')
        self.assertEquals(req['setrec'][0].bar, 'bar')
        self.assertEquals(req['setrec'][1].foo, 'spam')
        self.assertEquals(req['setrec'][1].bar, 'eggs')

    def testMarshallIntoSequences(self):
        inputs = (
            ('ilist:int:list', '1'), ('ilist:int:list', '2'),
            ('ilist:list:int', '3'),
            ('ftuple:float:tuple', '1.0'), ('ftuple:float:tuple', '1.1'),
            ('ftuple:tuple:float', '1.2'),
            ('tlist:tokens:list', 'one two'), ('tlist:list:tokens', '3 4'))
        req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEquals(formkeys, ['ftuple', 'ilist', 'tlist'])

        self.assertEquals(req['ilist'], [1, 2, 3])
        self.assertEquals(req['ftuple'], (1.0, 1.1, 1.2))
        self.assertEquals(req['tlist'], [['one', 'two'], ['3', '4']])

    def testRecordsWithSequences(self):
        inputs = (
            ('onerec.name:record', 'foo'),
            ('onerec.tokens:tokens:record', 'one two'),
            ('onerec.ints:int:record', '1'),
            ('onerec.ints:int:record', '2'),

            ('setrec.name:records', 'first'),
            ('setrec.ilist:list:int:records', '1'),
            ('setrec.ilist:list:int:records', '2'),
            ('setrec.ituple:tuple:int:records', '1'),
            ('setrec.ituple:tuple:int:records', '2'),
            ('setrec.name:records', 'second'),
            ('setrec.ilist:list:int:records', '1'),
            ('setrec.ilist:list:int:records', '2'),
            ('setrec.ituple:tuple:int:records', '1'),
            ('setrec.ituple:tuple:int:records', '2'))
        req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEquals(formkeys, ['onerec', 'setrec'])

        self.assertEquals(req['onerec'].name, 'foo')
        self.assertEquals(req['onerec'].tokens, ['one', 'two'])
        # Implicit sequences and records don't mix.
        self.assertEquals(req['onerec'].ints, 2)

        self.assertEquals(len(req['setrec']), 2)
        self.assertEquals(req['setrec'][0].name, 'first')
        self.assertEquals(req['setrec'][1].name, 'second')

        for i in range(2):
            self.assertEquals(req['setrec'][i].ilist, [1, 2])
            self.assertEquals(req['setrec'][i].ituple, (1, 2))

    def testDefaults(self):
        inputs = (
            ('foo:default:int', '5'), 

            ('alist:int:default', '3'),
            ('alist:int:default', '4'),
            ('alist:int:default', '5'),
            ('alist:int', '1'),
            ('alist:int', '2'),

            ('explicitlist:int:list:default', '3'),
            ('explicitlist:int:list:default', '4'),
            ('explicitlist:int:list:default', '5'),
            ('explicitlist:int:list', '1'),
            ('explicitlist:int:list', '2'),

            ('bar.spam:record:default', 'eggs'),
            ('bar.foo:record:default', 'foo'),
            ('bar.foo:record', 'baz'),

            ('setrec.spam:records:default', 'eggs'),
            ('setrec.foo:records:default', 'foo'),
            ('setrec.foo:records', 'baz'),
            ('setrec.foo:records', 'ham'),
            )
        req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEquals(formkeys, ['alist', 'bar', 'explicitlist', 'foo',
            'setrec'])

        self.assertEquals(req['alist'], [1, 2, 3, 4, 5])
        self.assertEquals(req['explicitlist'], [1, 2, 3, 4, 5])

        self.assertEquals(req['foo'], 5)
        self.assertEquals(req['bar'].spam, 'eggs')
        self.assertEquals(req['bar'].foo, 'baz')

        self.assertEquals(len(req['setrec']), 2)
        self.assertEquals(req['setrec'][0].spam, 'eggs')
        self.assertEquals(req['setrec'][0].foo, 'baz')
        self.assertEquals(req['setrec'][1].spam, 'eggs')
        self.assertEquals(req['setrec'][1].foo, 'ham')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RecordTests, 'test'))
    suite.addTest(unittest.makeSuite(ProcessInputsTests, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main()
