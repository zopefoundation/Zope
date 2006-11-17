from pprint import pprint
from time import time
from unittest import TestCase,TestSuite,makeSuite

class DummyDB:

    conn_num = 1
    
    def query(self,*args):
        return ('result for:',)+args

    def hook_method(self):
        conn_to_use = 'conn'+str(self.conn_num)
        self.conn_num += 1
        return conn_to_use

class DummyTime:

    def __init__(self,t):
        self.t = float(t)

    def __call__(self):
        return self.t
    
class TestCaching(TestCase):

    echo = False
    
    def setUp(self):
        from Shared.DC.ZRDB import DA
        self.DA = DA
        self.da = DA.DA('da','title','conn_id','arg1 arg2','some sql')
        # set the da's caching parameters
        self.da.cache_time_ = 10
        self.da.max_cache_ = 2

    def _do_query(self,query,time):
        try:
            self.DA.time = DummyTime(time)
            result = self.da._cached_result(DummyDB(),query)
        finally:
            self.DA.time = time
        self.assertEqual(result,('result for:',)+query)

    def _check_mapping(self,expected,actual):
        missing = []
        extra = []
        different = []
        for key,value in expected.items():
            try:
                ai = actual[key]
            except KeyError:
                missing.append(key)
            else:
                if ai!=value:
                    different.append('%r: %r != %r' % (key,value,ai))
        for key in actual.keys():
            try:
                expected[key]
            except KeyError:
                extra.append(key)
        result = []
        if different:
            different.sort()
            result.append("Mismatching, key: (expected != actual):")
            for r in different:
                result.append(r)
        if missing:
            missing.sort()
            result.append("The following keys were missing from actual:")
            for r in missing:
                result.append(repr(r))
        if extra:
            extra.sort()
            result.append("The following extra keys were found in actual:")
            for r in extra:
                result.append(repr(r))
        return result
        
    def _check_cache(self,cache,tcache):
        if self.echo:
            print "cache:"
            pprint(self.da._v_cache[0])
            print "tcache:"
            pprint(self.da._v_cache[1])
            print
        result = []
        r = self._check_mapping(cache,self.da._v_cache[0])
        if r:
            result.append("cache didn't match expected:")
            result.extend(r)
        r = self._check_mapping(tcache,self.da._v_cache[1])
        if r:
            result.append("tcache didn't match expected:")
            result.extend(r)
        if result:
            self.fail('\n\n'+'\n'.join(result))
        
    def test_same_query_different_seconds(self):
        # this tests a sequence set of requests for the same
        # query, but where the item returned is always in the cache
        self._check_cache({},{})
        for t in range(1,6):
            self._do_query(('query',),t)
            self._check_cache(
                {('query', '\nDBConnId: None'): (1,('result for:', 'query'))},
                {1: ('query', '\nDBConnId: None')}
                )

    def test_same_query_same_second(self):
        # this tests a sequence set of requests for the same
        # query, but where the item returned is always in the cache
        # and where the queries all occur in the same second, so
        # tickling the potential cache time rounding problem
        self._check_cache({},{})
        for t in range(11,16,1):
            t = float(t)/10
            self._do_query(('query',),t)
            self._check_cache(
                {('query', '\nDBConnId: None'): (1.1,('result for:', 'query'))},
                {1: ('query', '\nDBConnId: None')}
                )

    def test_different_queries_different_second(self):
        # This tests different queries being fired into the cache
        # in sufficient volume to excercise the purging code
        # XXX this demonstrates newer cached material being incorrectly
        #     dumped due to the replacement of Bucket with dict
        self._check_cache({},{})
        # one
        self._do_query(('query1',),1.1)
        self._check_cache(
            {('query1', '\nDBConnId: None'): (1.1,('result for:', 'query1'))},
            {1: ('query1', '\nDBConnId: None')}
            )
        # two
        self._do_query( ('query2',),3.2)
        self._check_cache(
            {('query1', '\nDBConnId: None'): (1.1,('result for:', 'query1')),
             ('query2', '\nDBConnId: None'): (3.2,('result for:', 'query2')),},
            {1: ('query1', '\nDBConnId: None'),
             3: ('query2', '\nDBConnId: None'),}
            )
        # three
        self._do_query(('query3',),4.3)
        self._check_cache(
            {('query1', '\nDBConnId: None'): (1.1,('result for:', 'query1')),
             ('query2', '\nDBConnId: None'): (3.2,('result for:', 'query2')),
             ('query3', '\nDBConnId: None'): (4.3,('result for:', 'query3')),},
            {1: ('query1', '\nDBConnId: None'),
             3: ('query2', '\nDBConnId: None'),
             4: ('query3', '\nDBConnId: None'),}
            )
        # four - now we drop our first cache entry, this is an off-by-one error
        self._do_query(('query4',),8.4)
        self._check_cache(
            {('query2', '\nDBConnId: None'): (3.2,('result for:', 'query2')),
             ('query3', '\nDBConnId: None'): (4.3,('result for:', 'query3')),
             ('query4', '\nDBConnId: None'): (8.4,('result for:', 'query4')),},
            {3: ('query2', '\nDBConnId: None'),
             4: ('query3', '\nDBConnId: None'),
             8: ('query4', '\nDBConnId: None'),}
            )
        # five - now we drop another cache entry
        self._do_query(('query5',),9.5)
        # XXX oops - because dicts have an arbitary ordering, we dumped the wrong key!
        self._check_cache(
            {('query3', '\nDBConnId: None'): (4.3,('result for:', 'query3')),
             ('query2', '\nDBConnId: None'): (3.2,('result for:', 'query2')),
             ('query5', '\nDBConnId: None'): (9.5,('result for:', 'query5')),},
            {4: ('query3', '\nDBConnId: None'),
             3: ('query2', '\nDBConnId: None'),
             9: ('query5', '\nDBConnId: None'),}
            )
        
    def test_different_queries_same_second(self):
        # This tests different queries being fired into the cache
        # in the same second.
        # XXX The demonstrates a memory leak in the cache code
        self._check_cache({},{})
        # one
        self._do_query(('query1',),1.0)
        self._check_cache(
            {('query1', '\nDBConnId: None'): (1.0,('result for:', 'query1'))},
            {1: ('query1', '\nDBConnId: None')}
            )
        # two
        self._do_query( ('query2',),1.1)
        self._check_cache(
            {('query1', '\nDBConnId: None'): (1.0,('result for:', 'query1')),
             ('query2', '\nDBConnId: None'): (1.1,('result for:', 'query2')),},
            {1.0: ('query2', '\nDBConnId: None'),}
            )
        # three
        self._do_query(('query3',),1.2)
        self._check_cache(
            {('query1', '\nDBConnId: None'): (1,('result for:', 'query1')),
             ('query2', '\nDBConnId: None'): (1.1,('result for:', 'query2')),
             ('query3', '\nDBConnId: None'): (1.2,('result for:', 'query3')),},
            {1: ('query3', '\nDBConnId: None'),}
            )
        # four - now we drop our first cache entry, this is an off-by-one error
        self._do_query(('query4',),1.3)
        self._check_cache(
            # XXX - oops, why is query1 here still?
            {('query1', '\nDBConnId: None'): (1,('result for:', 'query1')),
             ('query2', '\nDBConnId: None'): (1.1,('result for:', 'query2')),
             ('query3', '\nDBConnId: None'): (1.2,('result for:', 'query3')),
             ('query4', '\nDBConnId: None'): (1.3,('result for:', 'query4')),},
            {1: ('query4', '\nDBConnId: None'),}
            )
        # five - now we drop another cache entry
        self._do_query(('query5',),1.4)
        self._check_cache(
            # XXX - oops, why are query1 and query2 here still?
            {('query1', '\nDBConnId: None'): (1,('result for:', 'query1')),
             ('query2', '\nDBConnId: None'): (1.1,('result for:', 'query2')),
             ('query3', '\nDBConnId: None'): (1.2,('result for:', 'query3')),
             ('query4', '\nDBConnId: None'): (1.3,('result for:', 'query4')),
             ('query5', '\nDBConnId: None'): (1.4,('result for:', 'query5')),},
            {1: ('query5', '\nDBConnId: None'),}
            )

    def test_connection_hook(self):
        # XXX excercises the nonsense of the connection id cache descriminator
        self._do_query(('query1',),1.1)
        # XXX this should be '\nDBConnId: conn_id'
        self._check_cache(
            {('query1', '\nDBConnId: None'): (1.1,('result for:', 'query1'))},
            {1: ('query1', '\nDBConnId: None')}
            )
        del self.da._v_cache
        self.da.connection_hook='hook_method'
        # XXX this should be '\nDBConnId: conn1'
        self._do_query(('query1',),1.1)
        self._check_cache(
            {('query1', '\nDBConnId: hook_method'): (1.1,('result for:', 'query1'))},
            {1: ('query1', '\nDBConnId: hook_method')}
            )
        del self.da._v_cache
        # XXX this should be '\nDBConnId: conn2'
        self._do_query(('query1',),1.1)
        self._check_cache(
            {('query1', '\nDBConnId: hook_method'): (1.1,('result for:', 'query1'))},
            {1: ('query1', '\nDBConnId: hook_method')}
            )
        
class DummyDA:

    def __call__(self):
        # we return None here, because this should never actually be called
        return None

    sql_quote__ = "I don't know what this is."

class Hook:

    conn_num = 1
    
    def __call__(self):
        conn_to_use = 'conn'+str(self.conn_num)
        self.conn_num += 1
        return conn_to_use

class TestCacheKeys(TestCase):

    def _cached_result(self,DB__,query):
        self.cache_key = query
        # we return something that can be safely turned into an empty Result
        return ((),())
        
    def setUp(self):
        from Shared.DC.ZRDB.DA import DA
        self.da = DA('da','title','conn_id','arg1 arg2','some sql')
        self.da._cached_result = self._cached_result
        self.da.conn_id = DummyDA()
        # These need to be set so DA.__call__ tries for a cached result
        self.da.cache_time_ = 1
        self.da.max_cache_ = 1

    def test_default(self):
        self.da()
        self.assertEqual(self.cache_key,('some sql',1000))
        
    def test_different_max_rows(self):
        self.da.max_rows_ = 123
        self.da()
        self.assertEqual(self.cache_key,('some sql',123))
        
    def test_connection_hook(self):
        self.da.connection_hook = 'hook_method'
        self.da.hook_method = Hook()
        self.da.conn1 = DummyDA()
        self.da()
        # XXX the connection id should be added to the cache key here
        self.assertEqual(self.cache_key,('some sql',1000))
        self.da.conn2 = DummyDA()
        self.da()
        # XXX the connection id should be added to the cache key here
        self.assertEqual(self.cache_key,('some sql',1000))
        
def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(TestCaching))
    suite.addTest(makeSuite(TestCacheKeys))
    return suite
