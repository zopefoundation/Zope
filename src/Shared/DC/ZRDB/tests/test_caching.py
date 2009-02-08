from pprint import pprint
from time import time
from unittest import TestCase,TestSuite,makeSuite

class DummyDB:

    conn_num = 1

    result = None
    
    def query(self,query,max_rows):
        if self.result:
            return self.result
        return 'result for ' + query

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

    def _do_query(self,query,t):
        try:
            self.DA.time = DummyTime(t)
            result = self.da._cached_result(DummyDB(),query,1,'conn_id')
        finally:
            self.DA.time = time
        self.assertEqual(result,'result for '+query)

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
        
    def test_bad_aquisition(self):
        # checks that something called _v_cache isn't acquired from anywhere
        from ExtensionClass import Base
        class Dummy(Base):
            _v_cache = 'muhahaha'
        obj = Dummy()
        self.da = self.da.__of__(obj)
        del self.da._v_cache
        self._do_query('query',1)
        
    def test_same_query_different_seconds(self):
        # this tests a sequence of requests for the same
        # query, but where the item returned is always in the cache
        self._check_cache({},{})
        for t in range(1,6):
            self._do_query('query',t)
            self._check_cache(
                {('query',1,'conn_id'): (1,'result for query')},
                {1: ('query',1,'conn_id')}
                )

    def test_same_query_same_second(self):
        # this tests a sequence set of requests for the same
        # query, but where the item returned is always in the cache
        # and where the queries all occur in the same second
        self._check_cache({},{})
        for t in range(11,16,1):
            t = float(t)/10
            self._do_query('query',t)
            self._check_cache(
                {('query',1,'conn_id'): (1.1,'result for query')},
                {1.1: ('query',1,'conn_id')}
                )

    def test_different_queries_different_second(self):
        # This tests different queries being fired into the cache
        # in sufficient volume to excercise the purging code
        self._check_cache({},{})
        # one
        self._do_query('query1',1.1)
        self._check_cache(
            {('query1',1,'conn_id'): (1.1,'result for query1')},
            {1.1: ('query1',1,'conn_id')}
            )
        # two
        self._do_query( 'query2',3.2)
        self._check_cache(
            {('query1',1,'conn_id'): (1.1,'result for query1'),
             ('query2',1,'conn_id'): (3.2,'result for query2'),},
            {1.1: ('query1',1,'conn_id'),
             3.2: ('query2',1,'conn_id'),}
            )
        # three - now we drop our first cache entry
        self._do_query('query3',4.3)
        self._check_cache(
            {('query2',1,'conn_id'): (3.2,'result for query2'),
             ('query3',1,'conn_id'): (4.3,'result for query3'),},
            {3.2: ('query2',1,'conn_id'),
             4.3: ('query3',1,'conn_id'),}
            )
        # four - now we drop our second cache entry
        self._do_query('query4',8.4)
        self._check_cache(
            {('query3',1,'conn_id'): (4.3,'result for query3'),
             ('query4',1,'conn_id'): (8.4,'result for query4'),},
            {4.3: ('query3',1,'conn_id'),
             8.4: ('query4',1,'conn_id'),}
            )
        
    def test_different_queries_same_second(self):
        # This tests different queries being fired into the cache
        # in the same second in sufficient quantities to exercise
        # the purging code
        self._check_cache({},{})
        # one
        self._do_query('query1',1.0)
        self._check_cache(
            {('query1',1,'conn_id'): (1.0,'result for query1')},
            {1.0: ('query1',1,'conn_id')}
            )
        # two
        self._do_query( 'query2',1.1)
        self._check_cache(
            {('query1',1,'conn_id'): (1.0,'result for query1'),
             ('query2',1,'conn_id'): (1.1,'result for query2'),},
            {1.0: ('query1',1,'conn_id'),
             1.1: ('query2',1,'conn_id'),}
            )
        # three - now we drop our first cache entry
        self._do_query('query3',1.2)
        self._check_cache(
            {('query2',1,'conn_id'): (1.1,'result for query2'),
             ('query3',1,'conn_id'): (1.2,'result for query3'),},
            {1.1: ('query2',1,'conn_id'),
             1.2: ('query3',1,'conn_id'),}
            )
        # four - now we drop another cache entry
        self._do_query('query4',1.3)
        self._check_cache(
            {('query3',1,'conn_id'): (1.2,'result for query3'),
             ('query4',1,'conn_id'): (1.3,'result for query4'),},
            {1.2: ('query3',1,'conn_id'),
             1.3: ('query4',1,'conn_id'),}
            )

    def test_time_tcache_expires(self):
        # This tests that once the cache purging code is triggered,
        # it will actively hoover out all expired cache entries
        
        # the first query gets cached
        self._do_query('query1',1)
        self._check_cache(
            {('query1',1,'conn_id'): (1,'result for query1')},
            {1: ('query1',1,'conn_id')}
            )
        # the 2nd gets cached, the cache is still smaller than max_cache
        self._do_query('query2',2)
        self._check_cache(
            {('query1',1,'conn_id'): (1,'result for query1'),
             ('query2',1,'conn_id'): (2,'result for query2')},
            {1: ('query1',1,'conn_id'),
             2:('query2',1,'conn_id')}
            )
        # the 3rd trips the max_cache trigger, so both our old queries get
        # dumped because they are past their expiration time
        self._do_query('query',23)
        self._check_cache(
            {('query',1,'conn_id'): (23,'result for query')},
            {23:('query',1,'conn_id')}
            )
    
    def test_time_refreshed_cache(self):
        # This tests that when a cached query is expired when it comes
        # to check for a cached entry for that query, the stale entry is
        # removed and replaced with a fresh entry.
        
        # the first query gets cached
        self._do_query('query1',1)
        self._check_cache(
            {('query1',1,'conn_id'): (1,'result for query1')},
            {1: ('query1',1,'conn_id')}
            )
        # do the same query much later, so new one gets cached
        self._do_query('query1',12)
        self._check_cache(
            {('query1',1,'conn_id'): (12,'result for query1')},
            {12: ('query1',1,'conn_id')}
            )

class DummyDA:

    def __call__(self):
        conn = DummyDB()
        conn.result = ((),())
        return conn

    sql_quote__ = "I don't know what this is."

class Hook:

    conn_num = 1
    
    def __call__(self):
        conn_to_use = 'conn'+str(self.conn_num)
        self.conn_num += 1
        return conn_to_use

class TestCacheKeys(TestCase):
    # These tests check that the keys used for caching are unique
    # in the right ways.

    def _cached_result(self,DB__,query,row_count,conn_id):
        self.cache_key = query,row_count,conn_id
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
        self.assertEqual(self.cache_key,('some sql',1000,'conn_id'))
        
    def test_different_max_rows(self):
        self.da.max_rows_ = 123
        self.da()
        self.assertEqual(self.cache_key,('some sql',123,'conn_id'))
        
    def test_connection_hook(self):
        self.da.connection_hook = 'hook_method'
        self.da.hook_method = Hook()
        self.da.conn1 = DummyDA()
        self.da()
        self.assertEqual(self.cache_key,('some sql',1000,'conn1'))
        self.da.conn2 = DummyDA()
        self.da()
        self.assertEqual(self.cache_key,('some sql',1000,'conn2'))

class TestFullChain(TestCase):
    # This exercises both DA.__call__ and DA._cached_result.

    def setUp(self):
        from Shared.DC.ZRDB.DA import DA
        self.da = DA('da','title','conn_id','arg1 arg2','some sql')        
        self.da.conn_id = DummyDA()
        
    def test_args_match(self):
        # This checks is that DA._cached_result's call signature
        # matches that expected by DA.__call__

        # These need to be set so DA.__call__ tries for a cached result
        self.da.cache_time_ = 1
        self.da.max_cache_ = 1
        # the actual test, will throw exceptions if things aren't right
        self.da()

    def test_cached_result_not_called_for_no_caching(self):
        # blow up the _cached_result method on our
        # test instance
        self.da._cached_result = None
        # check we never get there with the default "no cachine"
        self.da()
        # turn caching on
        self.da.cache_time_ = 1
        self.da.max_cache_ = 1
        # check that we get an exception
        self.assertRaises(TypeError,self.da)
        
def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(TestCaching))
    suite.addTest(makeSuite(TestCacheKeys))
    suite.addTest(makeSuite(TestFullChain))
    return suite
