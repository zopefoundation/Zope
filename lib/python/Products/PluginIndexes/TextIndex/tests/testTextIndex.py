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

import sys, os, unittest
from glob import glob
import zLOG

def log_write(subsystem, severity, summary, detail, error):
    if severity >= zLOG.PROBLEM:
        assert 0, "%s(%s): %s" % (subsystem, severity, summary)


import ZODB, ZODB.DemoStorage, ZODB.FileStorage
from Products.PluginIndexes.TextIndex import TextIndex
from Products.PluginIndexes.TextIndex import GlobbingLexicon

class Dummy:

    def __init__( self, text ):
        self._text = text

    def text( self ):
        return self._text

    def __str__( self ):
        return '<Dummy: %s>' % self._text

    __repr__ = __str__

class Tests(unittest.TestCase):

    def setUp(self):
        self.index=TextIndex.TextIndex('text')
        self.doc=Dummy(text='this is the time, when all good zopes')
        self.old_log_write = zLOG.log_write
        zLOG.log_write=log_write


    def dbopen(self):
        n = 'fs_tmp__%s' % os.getpid()
        s = ZODB.FileStorage.FileStorage(n)
        db=self.db=ZODB.DB(s)
        self.jar=db.open()
        if not self.jar.root().has_key('index'):
            self.jar.root()['index']=TextIndex.TextIndex('text')
            get_transaction().commit()
        return self.jar.root()['index']

    def dbclose(self):
        self.jar.close()
        self.db.close()
        del self.jar
        del self.db

    def tearDown(self):
        get_transaction().abort()
        if hasattr(self, 'jar'):
            self.dbclose()
            for path in glob('fs_tmp__*'):
                os.remove(path)
        zLOG.log_write=self.old_log_write

    def checkSimpleAddDelete(self):
        "Check that we can add and delete an object without error"
        self.index.index_object(0, self.doc)
        self.index.index_object(1, self.doc)
        self.doc.text='spam is good, spam is fine, span span span'
        self.index.index_object(0, self.doc)
        self.index.unindex_object(0)

    def checkPersistentUpdate1(self):
        "Check simple persistent indexing"
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

    def checkPersistentUpdate2(self):
        "Check less simple persistent indexing"
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
        "Check a glob query"
        index=self.dbopen()
        index._lexicon = GlobbingLexicon.GlobbingLexicon()

        for i in range(len(self.sample_texts)):
            self.doc.text=self.sample_texts[i]
            index.index_object(i, self.doc)
            get_transaction().commit()

        self.dbclose()

        index=self.dbopen()

        r = list(index._apply_index(qmap)[0].keys())
        assert  r == rlist, r
        return index._apply_index

    def checkStarQuery(self):
        "Check a star query"
        self.globTest({'text':'m*n'}, [0,2])

    def checkAndQuery(self):
        "Check an AND query"
        self.globTest({'text':'time and country'}, [0,])

    def checkOrQuery(self):
        "Check an OR query"
        self.globTest({'text':'time or country'}, [0,1,6])

    def checkDefOrQuery(self):
        "Check a default OR query"
        self.globTest({'text':'time country'}, [0,1,6])

    def checkNearQuery(self):
        """Check a NEAR query.. (NOTE:ACTUALLY AN 'AND' TEST!!)"""
        # NEAR never worked, so Zopes post-2.3.1b3 define near to mean AND
        self.globTest({'text':'time ... country'}, [0,])

    def checkQuotesQuery(self):
        """Check a quoted query"""
        ai = self.globTest({'text':'"This is the time"'}, [0,])

        r = list(ai({'text':'"now is the time"'})[0].keys())
        assert  r == [], r

    def checkAndNotQuery(self):
        "Check an ANDNOT query"
        self.globTest({'text':'time and not country'}, [6,])

    def checkParenMatchingQuery(self):
        "Check a query with parens"
        ai = self.globTest({'text':'(time and country) men'}, [0,])

        r = list(ai({'text':'(time and not country) or men'})[0].keys())
        assert  r == [0, 6], r

    def checkTextIndexOperatorQuery(self):
        "Check a query with 'operator' in the request"
        self.globTest({'text': {'query': 'time men', 'operator':'and'}}, [0,])

    def checkNonExistentWord(self):
        """ Check for nonexistent word """
        self.globTest({'text':'zop'}, [])

    def checkComplexQuery1(self):
        """ Check complex query 1 """
        self.globTest({'text':'((?ount* or get) and not wait) '
                       '"been *ert*"'}, [0, 1, 5, 6])

    # same tests, unicode strings
    def checkStarQueryUnicode(self):
        "Check a star query (unicode)"
        self.globTest({'text':u'm*n'}, [0,2])

    def checkAndQueryUnicode(self):
        "Check an AND query (unicode)"
        self.globTest({'text':u'time and country'}, [0,])

    def checkOrQueryUnicode(self):
        "Check an OR query (unicode)"
        self.globTest({'text':u'time or country'}, [0,1,6])

    def checkDefOrQueryUnicode(self):
        "Check a default OR query (unicode)"
        self.globTest({'text':u'time country'}, [0,1,6])

    def checkNearQueryUnicode(self):
        """Check a NEAR query.. (NOTE:ACTUALLY AN 'AND' TEST!!) (unicode)"""
        # NEAR never worked, so Zopes post-2.3.1b3 define near to mean AND
        self.globTest({'text':u'time ... country'}, [0,])

    def checkQuotesQueryUnicode(self):
        """Check a quoted query (unicode)"""
        ai = self.globTest({'text':u'"This is the time"'}, [0,])

        r = list(ai({'text':'"now is the time"'})[0].keys())
        assert  r == [], r

    def checkAndNotQueryUnicode(self):
        "Check an ANDNOT query (unicode)"
        self.globTest({'text':u'time and not country'}, [6,])

    def checkParenMatchingQueryUnicode(self):
        "Check a query with parens (unicode)"
        ai = self.globTest({'text':u'(time and country) men'}, [0,])

        r = list(ai({'text':u'(time and not country) or men'})[0].keys())
        assert  r == [0, 6], r

    def checkTextIndexOperatorQueryUnicode(self):
        "Check a query with 'operator' in the request (unicode)"
        self.globTest({'text': {u'query': u'time men', 'operator':'and'}}, [0,])

    def checkNonExistentWordUnicode(self):
        """ Check for nonexistent word  (unicode)"""
        self.globTest({'text':u'zop'}, [])

    def checkComplexQuery1Unicode(self):
        """ Check complex query 1  (unicode)"""
        self.globTest({'text':u'((?ount* or get) and not wait) '
                       '"been *ert*"'}, [0, 1, 5, 6])


def test_suite():
    return unittest.makeSuite(Tests, 'check')

def main():
    unittest.TextTestRunner().run(test_suite())

def debug():
    test_suite().debug()

def pdebug():
    import pdb
    pdb.run('debug()')

if __name__=='__main__':
    if len(sys.argv) > 1:
        globals()[sys.argv[1]]()
    else:
        main()
