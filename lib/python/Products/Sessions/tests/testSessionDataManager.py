##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
import sys, os, time
if __name__ == "__main__":
    sys.path.insert(0, '../../..')
    #os.chdir('../../..')
from Testing import makerequest
import ZODB # in order to get Persistence.Persistent working
import Acquisition
from Acquisition import aq_base
from Products.Sessions.BrowserIdManager import BrowserIdManager
from Products.Sessions.SessionDataManager import \
    SessionDataManager, SessionDataManagerErr
from Products.Transience.Transience import \
    TransientObjectContainer, TransientObject
from Products.TemporaryFolder.TemporaryFolder import MountedTemporaryFolder
from ZODB.POSException import InvalidObjectReference, ConflictError
from DateTime import DateTime
from unittest import TestCase, TestSuite, TextTestRunner, makeSuite
import time, threading, whrandom
from cPickle import UnpickleableError
from ZODB.DemoStorage import DemoStorage
from OFS.Application import Application
import sys
sys.setcheckinterval(200)

tf_name = 'temp_folder'
idmgr_name = 'browser_id_manager'
toc_name = 'temp_transient_container'

stuff = {}

def _getDB():
    db = stuff.get('db')
    if not db:
        ds = DemoStorage(quota=(1<<20))
        db = ZODB.DB(ds, pool_size=60)
        conn = db.open()
        root = conn.root()
        app = Application()
        root['Application']= app
        _populate(app)
        get_transaction().commit()
        stuff['db'] = db
        conn.close()
    return db

def _delDB():
    get_transaction().abort()
    del stuff['db']

class Foo(Acquisition.Implicit): pass

def _populate(app):
    bidmgr = BrowserIdManager(idmgr_name)
    tf = MountedTemporaryFolder(tf_name, title="Temporary Folder")
    toc = TransientObjectContainer(toc_name, title='Temporary '
        'Transient Object Container', timeout_mins=20)
    session_data_manager=SessionDataManager(id='session_data_manager',
        path='/'+tf_name+'/'+toc_name, title='Session Data Manager')

    try: app._delObject(idmgr_name)
    except AttributeError: pass

    try: app._delObject(tf_name)
    except AttributeError: pass

    try: app._delObject('session_data_manager')
    except AttributeError: pass

    app._setObject(idmgr_name, bidmgr)

    app._setObject('session_data_manager', session_data_manager)

    app._setObject(tf_name, tf)
    get_transaction().commit()

    app.temp_folder._setObject(toc_name, toc)
    get_transaction().commit()

class TestBase(TestCase):
    def setUp(self):
        db = _getDB()
        conn = db.open()
        root = conn.root()
        self.app = makerequest.makerequest(root['Application'])
        timeout = self.timeout = 1

    def tearDown(self):
        _delDB()
        del self.app

class TestSessionManager(TestBase):
    def testHasId(self):
        assert self.app.session_data_manager.id == 'session_data_manager'

    def testHasTitle(self):
        assert self.app.session_data_manager.title == 'Session Data Manager'

    def testGetSessionDataNoCreate(self):
        sd = self.app.session_data_manager.getSessionData(0)
        assert sd is None, repr(sd)

    def testGetSessionDataCreate(self):
        sd = self.app.session_data_manager.getSessionData(1)
        assert sd.__class__ is TransientObject, repr(sd)

    def testHasSessionData(self):
        sd = self.app.session_data_manager.getSessionData()
        assert self.app.session_data_manager.hasSessionData()

    def testNewSessionDataObjectIsValid(self):
        sdType = type(TransientObject(1))
        sd = self.app.session_data_manager.getSessionData()
        assert type(getattr(sd, 'aq_base', sd)) is sdType
        assert not hasattr(sd, '_invalid')

    def testInvalidateSessionDataObject(self):
        sd = self.app.session_data_manager.getSessionData()
        sd.invalidate()
        assert hasattr(sd, '_invalid')
        
    def testSessionTokenIsSet(self):
        sd = self.app.session_data_manager.getSessionData()
        mgr = getattr(self.app, idmgr_name)
        assert mgr.hasToken()

    def testGetSessionDataByKey(self):
        sd = self.app.session_data_manager.getSessionData()
        mgr = getattr(self.app, idmgr_name)
        token = mgr.getToken()
        bykeysd = self.app.session_data_manager.getSessionDataByKey(token)
        assert sd == bykeysd, (sd, bykeysd, token)

    def testBadExternalSDCPath(self):
        self.app.session_data_manager.REQUEST['REQUEST_METHOD'] = 'GET' # fake out webdav
        self.app.session_data_manager.setContainerPath('/fudgeffoloo')
        try:
            self.app.session_data_manager.getSessionData()
        except SessionDataManagerErr:
            pass
        else:
            assert 1 == 2, self.app.session_data_manager.getSessionDataContainerPath()

    def testInvalidateSessionDataObject(self):
        sd = self.app.session_data_manager.getSessionData()
        sd['test'] = 'Its alive!  Alive!'
        sd.invalidate()
        assert not self.app.session_data_manager.getSessionData().has_key('test')

    def testGhostUnghostSessionManager(self):
        get_transaction().commit()
        sd = self.app.session_data_manager.getSessionData()
        sd.set('foo', 'bar')
        self.app.session_data_manager._p_changed = None
        get_transaction().commit()
        assert self.app.session_data_manager.getSessionData().get('foo') == 'bar'

    def testSubcommit(self):
        sd = self.app.session_data_manager.getSessionData()
        sd.set('foo', 'bar')
        assert get_transaction().commit(1) == None

    def testForeignObject(self):
        self.assertRaises(InvalidObjectReference, self._foreignAdd)

    def _foreignAdd(self):
        ob = self.app.session_data_manager
        sd = self.app.session_data_manager.getSessionData()
        sd.set('foo', ob)
        get_transaction().commit()

    def testAqWrappedObjectsFail(self):
        a = Foo()
        b = Foo()
        aq_wrapped = a.__of__(b)
        sd = self.app.session_data_manager.getSessionData()
        sd.set('foo', aq_wrapped)
        self.assertRaises(UnpickleableError, get_transaction().commit)

class TestMultiThread(TestCase):
    def testNonOverlappingSids(self):
        readers = []
        writers = []
        readiters = 20
        writeiters = 5
        readout = []
        writeout = []
        numreaders = 20
        numwriters = 5
        sdm_name = 'session_data_manager'
        db = _getDB()
        for i in range(numreaders):
            thread = ReaderThread(db, readiters, sdm_name)
            readers.append(thread)
        for i in range(numwriters):
            thread = WriterThread(db, writeiters, sdm_name)
            writers.append(thread)
        for thread in readers:
            thread.start()
            time.sleep(0.1)
        for thread in writers:
            thread.start()
            time.sleep(0.1)
        while threading.activeCount() > 1:
            time.sleep(1)
        
        for thread in readers:
            assert thread.out == [], thread.out

    def testOverlappingSids(self):
        readers = []
        writers = []
        readiters = 20
        writeiters = 5
        readout = []
        writeout = []
        numreaders = 20
        numwriters = 5
        sdm_name = 'session_data_manager'
        db = _getDB()
        for i in range(numreaders):
            thread = ReaderThread(db, readiters, sdm_name)
            readers.append(thread)
        for i in range(numwriters):
            thread = WriterThread(db, writeiters, sdm_name)
            writers.append(thread)
        for thread in readers:
            thread.start()
            time.sleep(0.1)
        for thread in writers:
            thread.start()
            time.sleep(0.1)
        while threading.activeCount() > 1:
            time.sleep(1)
        
        for thread in readers:
            assert thread.out == [], thread.out

class BaseReaderWriter(threading.Thread):
    def __init__(self, db, iters, sdm_name):
        self.conn = db.open()
        self.app = self.conn.root()['Application']
        self.app = makerequest.makerequest(self.app)
        token = self.app.browser_id_manager._getNewToken()
        self.app.REQUEST.session_token_ = token
        self.iters = iters
        self.sdm_name = sdm_name
        self.out = []
        threading.Thread.__init__(self)

    def run(self):
        i = 0
        try:
            while 1:
                try:
                    self.run1()
                    return
                except ConflictError:
                    i = i + 1
                    #print "conflict %d" % i
                    if i > 3: raise
        finally:
            self.conn.close()
            del self.app
            
class ReaderThread(BaseReaderWriter):
    def run1(self):
        session_data_manager = getattr(self.app, self.sdm_name)
        data = session_data_manager.getSessionData(create=1)
        t = time.time()
        data[t] = 1
        get_transaction().commit()
        for i in range(self.iters):
            data = session_data_manager.getSessionData()
            if not data.has_key(t):
                self.out.append(1)
            time.sleep(whrandom.choice(range(3)))
            get_transaction().commit()

class WriterThread(BaseReaderWriter):
    def run1(self):
        session_data_manager = getattr(self.app, self.sdm_name)
        for i in range(self.iters):
            data = session_data_manager.getSessionData()
            data[time.time()] = 1
            n = whrandom.choice(range(3))
            time.sleep(n)
            if n % 2 == 0:
                get_transaction().commit()
            else:
                get_transaction().abort()

def test_suite():
    test_datamgr = makeSuite(TestSessionManager, 'test')
    test_multithread = makeSuite(TestMultiThread, 'test')
    suite = TestSuite((test_datamgr, test_multithread))
    return suite

if __name__ == '__main__':
    runner = TextTestRunner(verbosity=9, descriptions=9)
    runner.run(test_suite())

