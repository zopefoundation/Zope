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
import zLOG

def log_write(subsystem, severity, summary, detail, error):
    if severity >= zLOG.PROBLEM:
        assert 0, "%s(%s): %s" % (subsystem, severity, summary)


import ZODB
from ZODB.MappingStorage import MappingStorage
import transaction

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

    db = None
    jar = None

    def setUp(self):
        self.index=TextIndex.TextIndex('text')
        self.doc=Dummy(text='this is the time, when all good zopes')
        self.old_log_write = zLOG.log_write
        zLOG.log_write=log_write


    def dbopen(self):
        if self.db is None:
            s = MappingStorage()
            self.db = ZODB.DB(s)
        db = self.db
        if self.jar is not None:
            raise RuntimeError, 'test needs to dbclose() before dbopen()'
        jar = db.open()
        self.jar = jar
        if not jar.root().has_key('index'):
            jar.root()['index'] = TextIndex.TextIndex('text')
            transaction.commit()
        return jar.root()['index']

    def dbclose(self):
        self.jar.close()
        self.jar = None

    def tearDown(self):
        transaction.abort()
        if self.jar is not None:
            self.dbclose()
        if self.db is not None:
            self.db.close()
            self.db = None
        zLOG.log_write=self.old_log_write

    def checkSimpleAddDelete(self):
        self.index.index_object(0, self.doc)
        self.index.index_object(1, self.doc)
        self.doc.text='spam is good, spam is fine, span span span'
        self.index.index_object(0, self.doc)
        self.index.unindex_object(0)

    def checkPersistentUpdate1(self):
        # Check simple persistent indexing
        index=self.dbopen()

        self.doc.text='this is the time, when all good zopes'
        index.index_object(0, self.doc)
        transaction.commit()

        self.doc.text='time waits for no one'
        index.index_object(1, self.doc)
        transaction.commit()
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
        # Check less simple persistent indexing
        index=self.dbopen()

        self.doc.text='this is the time, when all good zopes'
        index.index_object(0, self.doc)
        transaction.commit()

        self.doc.text='time waits for no one'
        index.index_object(1, self.doc)
        transaction.commit()

        self.doc.text='the next task is to test'
        index.index_object(3, self.doc)
        transaction.commit()

        self.doc.text='time time'
        index.index_object(2, self.doc)
        transaction.commit()
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
            transaction.commit()

        self.dbclose()

        index=self.dbopen()

        r = list(index._apply_index(qmap)[0].keys())
        assert  r == rlist, r
        return index._apply_index

    def checkStarQuery(self):
        self.globTest({'text':'m*n'}, [0,2])

    def checkAndQuery(self):
        self.globTest({'text':'time and country'}, [0,])

    def checkOrQuery(self):
        self.globTest({'text':'time or country'}, [0,1,6])

    def checkDefaultOrQuery(self):
        self.globTest({'text':'time country'}, [0,1,6])

    def checkNearQuery(self):
        # Check a NEAR query.. (NOTE:ACTUALLY AN 'AND' TEST!!)
        # NEAR never worked, so Zopes post-2.3.1b3 define near to mean AND
        self.globTest({'text':'time ... country'}, [0,])

    def checkQuotesQuery(self):
        ai = self.globTest({'text':'"This is the time"'}, [0,])

        r = list(ai({'text':'"now is the time"'})[0].keys())
        assert  r == [], r

    def checkAndNotQuery(self):
        self.globTest({'text':'time and not country'}, [6,])

    def checkParenMatchingQuery(self):
        ai = self.globTest({'text':'(time and country) men'}, [0,])

        r = list(ai({'text':'(time and not country) or men'})[0].keys())
        assert  r == [0, 6], r

    def checkTextIndexOperatorQuery(self):
        self.globTest({'text': {'query': 'time men', 'operator':'and'}}, [0,])

    def checkNonExistentWord(self):
        self.globTest({'text':'zop'}, [])

    def checkComplexQuery1(self):
        self.globTest({'text':'((?ount* or get) and not wait) '
                       '"been *ert*"'}, [0, 1, 5, 6])

    # same tests, unicode strings
    def checkStarQueryUnicode(self):
        self.globTest({'text':u'm*n'}, [0,2])

    def checkAndQueryUnicode(self):
        self.globTest({'text':u'time and country'}, [0,])

    def checkOrQueryUnicode(self):
        self.globTest({'text':u'time or country'}, [0,1,6])

    def checkDefaultOrQueryUnicode(self):
        self.globTest({'text':u'time country'}, [0,1,6])

    def checkNearQueryUnicode(self):
        # Check a NEAR query.. (NOTE:ACTUALLY AN 'AND' TEST!!) (unicode)
        # NEAR never worked, so Zopes post-2.3.1b3 define near to mean AND
        self.globTest({'text':u'time ... country'}, [0,])

    def checkQuotesQueryUnicode(self):
        ai = self.globTest({'text':u'"This is the time"'}, [0,])

        r = list(ai({'text':'"now is the time"'})[0].keys())
        assert  r == [], r

    def checkAndNotQueryUnicode(self):
        self.globTest({'text':u'time and not country'}, [6,])

    def checkParenMatchingQueryUnicode(self):
        ai = self.globTest({'text':u'(time and country) men'}, [0,])

        r = list(ai({'text':u'(time and not country) or men'})[0].keys())
        assert  r == [0, 6], r

    def checkTextIndexOperatorQueryUnicode(self):
        self.globTest({'text': {u'query': u'time men', 'operator':'and'}},
                      [0,])

    def checkNonExistentWordUnicode(self):
        self.globTest({'text':u'zop'}, [])

    def checkComplexQuery1Unicode(self):
        self.globTest({'text':u'((?ount* or get) and not wait) '
                       '"been *ert*"'}, [0, 1, 5, 6])


def test_suite():
    return unittest.makeSuite(Tests, 'check')

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
