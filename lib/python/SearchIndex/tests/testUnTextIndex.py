##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import unittest

from Testing.ZODButil import makeDB, cleanDB

import SearchIndex.UnTextIndex
import SearchIndex.GlobbingLexicon

class Tests(unittest.TestCase):

    def setUp(self):
        self.index=SearchIndex.UnTextIndex.UnTextIndex('text')
        self.doc=Dummy(text='this is the time, when all good zopes')
        catch_log_errors()

    def dbopen(self):
        db = self.db = makeDB()
        self.jar=db.open()
        if not self.jar.root().has_key('index'):
            self.jar.root()['index']=SearchIndex.UnTextIndex.UnTextIndex('text')
            get_transaction().commit()
        return self.jar.root()['index']

    def dbclose(self):
        self.jar.close()
        self.db.close()
        del self.jar
        del self.db

    def tearDown(self):
        ignore_log_errors()
        get_transaction().abort()
        if hasattr(self, 'jar'):
            self.dbclose()
            cleanDB()
        self.__dict__.clear()

    def testSimpleAddDelete(self):
        "Test that we can add and delete an object without error"
        self.index.index_object(0, self.doc)
        self.index.index_object(1, self.doc)
        self.doc.text='spam is good, spam is fine, span span span'
        self.index.index_object(0, self.doc)
        self.index.unindex_object(0)

    def testPersistentUpdate1(self):
        "Test simple persistent indexing"
        index=self.dbopen()

        self.doc.text='this is the time, when all good zopes'
        index.index_object(0, self.doc)
        get_transaction().commit()

        self.doc.text='time waits for no one'
        index.index_object(1, self.doc)
        get_transaction().commit()
        self.dbclose()

        index=self.dbopen()

        r = index._apply_index({})
        assert r==None

        r = index._apply_index({'text': 'python'})
        assert len(r) == 2 and r[1]==('text',), 'incorrectly not used'
        assert not r[0], "should have no results"

        r = index._apply_index({'text': 'time'})
        r=list(r[0].keys())
        assert  r == [0,1], r

    def testPersistentUpdate2(self):
        "Test less simple persistent indexing"
        index=self.dbopen()

        self.doc.text='this is the time, when all good zopes'
        index.index_object(0, self.doc)
        get_transaction().commit()

        self.doc.text='time waits for no one'
        index.index_object(1, self.doc)
        get_transaction().commit()

        self.doc.text='the next task is to test'
        index.index_object(3, self.doc)
        get_transaction().commit()

        self.doc.text='time time'
        index.index_object(2, self.doc)
        get_transaction().commit()
        self.dbclose()

        index=self.dbopen()

        r = index._apply_index({})
        assert r==None

        r = index._apply_index({'text': 'python'})
        assert len(r) == 2 and r[1]==('text',), 'incorrectly not used'
        assert not r[0], "should have no results"

        r = index._apply_index({'text': 'time'})
        r=list(r[0].keys())
        assert  r == [0,1,2], r



    sample_texts = [
        """This is the time for all good men to come to
        the aid of their country""",
        """ask not what your country can do for you,
        ask what you can do for your country""",
        """Man, I can't wait to get to Montross!""",
        """Zope Public License (ZPL) Version 1.0""",
        """Copyright (c) Digital Creations.  All rights reserved.""",
        """This license has been certified as Open Source(tm).""",
        """I hope I get to work on time""",
        ]

    def globTest(self, qmap, rlist):
        "Test a glob query"
        index = getattr(self, '_v_index', None)
        if index is None:
            index=self.dbopen()
            index._lexicon = SearchIndex.GlobbingLexicon.GlobbingLexicon()

            for i in range(len(self.sample_texts)):
                self.doc.text=self.sample_texts[i]
                index.index_object(i, self.doc)
                get_transaction().commit()

            self.dbclose()

            index = self._v_index = self.dbopen()

        r = list(index._apply_index(qmap)[0].keys())
        assert  r == rlist, r

    def testStarQuery(self):
        "Test a star query"
        self.globTest({'text':'m*n'}, [0,2])

    def testAndQuery(self):
        "Test an AND query"
        self.globTest({'text':'time and country'}, [0,])

    def testOrQuery(self):
        "Test an OR query"
        self.globTest({'text':'time or country'}, [0,1,6])

    def testDefOrQuery(self):
        "Test a default OR query"
        self.globTest({'text':'time country'}, [0,1,6])
        self.globTest({'text':'time good country'}, [0,1,6])

    def testNearQuery(self):
        """Test a NEAR query.. (NOTE:ACTUALLY AN 'AND' TEST!!)"""
        # NEAR never worked, so Zopes post-2.3.1b3 define near to mean AND
        self.globTest({'text':'time ... country'}, [0,])

    def testQuotesQuery(self):
        """Test a quoted query"""
        self.globTest({'text':'"This is the time"'}, [0,])
        self.globTest({'text':'"now is the time"'}, [])

    def testAndNotQuery(self):
        "Test an ANDNOT query"
        self.globTest({'text':'time and not country'}, [6,])

    def testParenMatchingQuery(self):
        "Test a query with parens"
        self.globTest({'text':'(time and country) men'}, [0,])
        self.globTest({'text':'(time and not country) or men'}, [0, 6])

    def testTextIndexOperatorQuery(self):
        "Test a query with 'textindex_operator' in the request"
        self.globTest({'text':'time men', 'textindex_operator':'and'}, [0,])

    def testNonExistentWord(self):
        """ Test for nonexistent word """
        self.globTest({'text':'zop'}, [])

    def testShortWord(self):
        """ Test for short word """
        self.globTest({'text':'to'}, [0, 2, 6])
        self.globTest({'text':'*to'}, [0, 2, 6])
        self.globTest({'text':'to*'}, [0, 2, 6])
        self.globTest({'text':'*to*'}, [0, 2, 6])

    def testComplexQuery1(self):
        """ Test complex query 1 """
        self.globTest({'text':'((?ount* or get) and not wait) '
                       '"been *ert*"'}, [0, 1, 5, 6])

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Tests),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
