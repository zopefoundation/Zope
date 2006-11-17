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
        
    def test_same_query_different_seconds(self):
        # this tests a sequence set of requests for the same
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
        # and where the queries all occur in the same second, so
        # tickling the potential cache time rounding problem
        self._check_cache({},{})
        for t in range(11,16,1):
            t = float(t)/10
            self._do_query('query',t)
            self._check_cache(
                {('query',1,'conn_id'): (1.1,'result for query')},
                {1: ('query',1,'conn_id')}
                )

    def test_different_queries_different_second(self):
        # This tests different queries being fired into the cache
        # in sufficient volume to excercise the purging code
        # XXX this demonstrates newer cached material being incorrectly
        #     dumped due to the replacement of Bucket with dict
        self._check_cache({},{})
        # one
        self._do_query('query1',1.1)
        self._check_cache(
            {('query1',1,'conn_id'): (1.1,'result for query1')},
            {1: ('query1',1,'conn_id')}
            )
        # two
        self._do_query( 'query2',3.2)
        self._check_cache(
            {('query1',1,'conn_id'): (1.1,'result for query1'),
             ('query2',1,'conn_id'): (3.2,'result for query2'),},
            {1: ('query1',1,'conn_id'),
             3: ('query2',1,'conn_id'),}
            )
        # three
        self._do_query('query3',4.3)
        self._check_cache(
            {('query1',1,'conn_id'): (1.1,'result for query1'),
             ('query2',1,'conn_id'): (3.2,'result for query2'),
             ('query3',1,'conn_id'): (4.3,'result for query3'),},
            {1: ('query1',1,'conn_id'),
             3: ('query2',1,'conn_id'),
             4: ('query3',1,'conn_id'),}
            )
        # four - now we drop our first cache entry, this is an off-by-one error
        self._do_query('query4',8.4)
        self._check_cache(
            {('query2',1,'conn_id'): (3.2,'result for query2'),
             ('query3',1,'conn_id'): (4.3,'result for query3'),
             ('query4',1,'conn_id'): (8.4,'result for query4'),},
            {3: ('query2',1,'conn_id'),
             4: ('query3',1,'conn_id'),
             8: ('query4',1,'conn_id'),}
            )
        # five - now we drop another cache entry
        self._do_query('query5',9.5)
        # XXX oops - because dicts have an arbitary ordering, we dumped the wrong key!
        self._check_cache(
            {('query3',1,'conn_id'): (4.3,'result for query3'),
             ('query2',1,'conn_id'): (3.2,'result for query2'),
             ('query5',1,'conn_id'): (9.5,'result for query5'),},
            {4: ('query3',1,'conn_id'),
             3: ('query2',1,'conn_id'),
             9: ('query5',1,'conn_id'),}
            )
        
    def test_different_queries_same_second(self):
        # This tests different queries being fired into the cache
        # in the same second.
        # XXX The demonstrates 2 memory leaks in the cache code
        self._check_cache({},{})
        # one
        self._do_query('query1',1.0)
        self._check_cache(
            {('query1',1,'conn_id'): (1.0,'result for query1')},
            {1: ('query1',1,'conn_id')}
            )
        # two
        self._do_query( 'query2',1.1)
        self._check_cache(
            # XXX oops, query1 is in the cache but it'll never be purged.
            {('query1',1,'conn_id'): (1.0,'result for query1'),
             ('query2',1,'conn_id'): (1.1,'result for query2'),},
            {1.0: ('query2',1,'conn_id'),}
            )
        # three
        self._do_query('query3',1.2)
        self._check_cache(
            # XXX oops, query1 and query2 are in the cache but will never be purged
            {('query1',1,'conn_id'): (1,'result for query1'),
             ('query2',1,'conn_id'): (1.1,'result for query2'),
             ('query3',1,'conn_id'): (1.2,'result for query3'),},
            {1: ('query3',1,'conn_id'),}
            )
        # four - now we drop our first cache entry, this is an off-by-one error
        self._do_query('query4',1.3)
        self._check_cache(
            # XXX - oops, why is query1 here still? see above ;-)
            {('query1',1,'conn_id'): (1,'result for query1'),
             ('query2',1,'conn_id'): (1.1,'result for query2'),
             ('query3',1,'conn_id'): (1.2,'result for query3'),
             ('query4',1,'conn_id'): (1.3,'result for query4'),},
            {1: ('query4',1,'conn_id'),}
            )
        # five - now we drop another cache entry
        self._do_query('query5',1.4)
        self._check_cache(
            # XXX - oops, why are query1 and query2 here still? see above ;-)
            {('query1',1,'conn_id'): (1,'result for query1'),
             ('query2',1,'conn_id'): (1.1,'result for query2'),
             ('query3',1,'conn_id'): (1.2,'result for query3'),
             ('query4',1,'conn_id'): (1.3,'result for query4'),
             ('query5',1,'conn_id'): (1.4,'result for query5'),},
            {1: ('query5',1,'conn_id'),}
            )

    def test_time_tcache_expires(self):
        # the first query gets cached
        self._do_query('query1',1)
        self._check_cache(
            {('query1',1,'conn_id'): (1,'result for query1')},
            {1: ('query1',1,'conn_id')}
            )
        # the 2nd gets cached, the cache is still smaller than max_cache / 2
        self._do_query('query2',12)
        self._check_cache(
            {('query1',1,'conn_id'): (1,'result for query1'),
             ('query2',1,'conn_id'): (12,'result for query2')},
            {1: ('query1',1,'conn_id'),
             12:('query2',1,'conn_id')}
            )
        # the 2rd trips the max_cache/2 trigger, so both our old queries get
        # dumped
        self._do_query('query',23)
        self._check_cache(
            {('query',1,'conn_id'): (23,'result for query')},
            {23:('query',1,'conn_id')}
            )
    
    def test_time_refreshed_cache(self):
        # the first query gets cached
        self._do_query('query1',1)
        self._check_cache(
            {('query1',1,'conn_id'): (1,'result for query1')},
            {1: ('query1',1,'conn_id')}
            )
        # do the same query much later, so new one gets cached
        # XXX memory leak as old tcache entry is left lying around
        self._do_query('query1',12)
        self._check_cache(
            {('query1',1,'conn_id'): (12,'result for query1')},
            {1: ('query1',1,'conn_id'), # XXX why is 1 still here?
             12: ('query1',1,'conn_id')}
            )
    def test_cachetime_doesnt_match_tcache_time(self):
        # get some old entries for one query in
        # (the time are carefully picked to give out-of-order dict keys)
        self._do_query('query1',4)
        self._do_query('query1',19)
        self._do_query('query1',44)
        self._check_cache(
            {('query1',1,'conn_id'): (44,'result for query1')},
            {4: ('query1',1,'conn_id'),
             19: ('query1',1,'conn_id'),
             44: ('query1',1,'conn_id')}
            )
        # now do another query
        self._do_query('query2',44.1)
        # XXX whoops, because {4:True,19:True,44:True}.keys()==[44,19,4]
        # the cache/tcache clearing code deletes the cache entry and
        # then tries to do it again later with an older tcache entry.
        # brian's patch in Dec 2000 works around this.
        self._do_query('query3',44.2)
        self._check_cache(
            {('query1',1,'conn_id'): (44,'result for query1'),
             ('query3',1,'conn_id'): (44.2,'result for query3')},
            {44: ('query3',1,'conn_id')}
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

    def test_full_chain(self):
        from Shared.DC.ZRDB.DA import DA
        self.da = DA('da','title','conn_id','arg1 arg2','some sql')        
        self.da.conn_id = DummyDA()
        # These need to be set so DA.__call__ tries for a cached result
        self.da.cache_time_ = 1
        self.da.max_cache_ = 1
        # run the method, exercising both DA.__call__ and DA._cached_result
        # currently all this checks is that DA._cached_result's call signature
        # matches that expected by DA.__call__
        self.da()
        
def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(TestCaching))
    suite.addTest(makeSuite(TestCacheKeys))
    suite.addTest(makeSuite(TestFullChain))
    return suite
