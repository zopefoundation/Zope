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

def _getApp():
    
    app = stuff.get('app', None)
    if not app:
        ds = DemoStorage(quota=(1<<20))
        db = ZODB.DB(ds, pool_size=60)
        conn = db.open()
        root = conn.root()
        app = Application()
        root['Application']= app
        get_transaction().commit()
        stuff['app'] = app
        stuff['conn'] = conn
        stuff['db'] = db
    return app

def _openApp():
    conn = stuff['db'].open()
    root = conn.root()
    app = root['Application']
    return conn, app

def _delApp():
    get_transaction().abort()
    stuff['conn'].close()
    del stuff['conn']
    del stuff['app']
    del stuff['db']

def f(sdo):
    pass

class Foo(Acquisition.Implicit): pass

class TestBase(TestCase):
    def setUp(self):
        self.app = makerequest.makerequest(_getApp())
        timeout = self.timeout = 1


        # Try to work around some testrunner snafus
        if 1 and __name__ is not '__main__':

            bidmgr = BrowserIdManager(idmgr_name)

            tf = MountedTemporaryFolder(tf_name, title="Temporary Folder")

            toc = TransientObjectContainer(toc_name, title='Temporary '
                'Transient Object Container', timeout_mins=20)

            session_data_manager=SessionDataManager(id='session_data_manager',
                path='/'+tf_name+'/'+toc_name, title='Session Data Manager')

            try: self.app._delObject(idmgr_name)
            except AttributeError: pass

            try: self.app._delObject(tf_name)
            except AttributeError: pass
            
            try: self.app._delObject('session_data_manager')
            except AttributeError: pass

            self.app._setObject(idmgr_name, bidmgr)
            self.app._setObject(tf_name, tf)

            get_transaction().commit()

            self.app.temp_folder._setObject(toc_name, toc)
            self.app._setObject('session_data_manager', session_data_manager)
            get_transaction().commit()

        # leans on the fact that these things exist by app init


##         admin = self.app.acl_users.getUser('admin')
##         if admin is None:
##             raise "Need to define an 'admin' user before running these tests"
##         admin = admin.__of__(self.app.acl_users)
##         self.app.session_data_manager.changeOwnership(admin)

    def tearDown(self):
        get_transaction().abort()
        #self.app._p_jar.close()
        #self.app = None
        _delApp()
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

    # Why would this have failed??  Not sure what it was meant to test
    #def testForeignObject(self):
    #    self.assertRaises(InvalidObjectReference, self._foreignAdd)

    #def _foreignAdd(self):
    #    ob = self.app.session_data_manager
    #    sd = self.app.session_data_manager.getSessionData()
    #    sd.set('foo', ob)
    #    get_transaction().commit()

    def testAqWrappedObjectsFail(self):
        a = Foo()
        b = Foo()
        aq_wrapped = a.__of__(b)
        sd = self.app.session_data_manager.getSessionData()
        sd.set('foo', aq_wrapped)
        self.assertRaises(UnpickleableError, get_transaction().commit)

class TestMultiThread(TestBase):
    def testNonOverlappingSids(self):
        readers = []
        writers = []
        readiters = 20
        writeiters = 5
        readout = []
        writeout = []
        numreaders = 20
        numwriters = 5
        #rlock = threading.Lock()
        rlock = DumboLock()
        sdm_name = 'session_data_manager'
        for i in range(numreaders):
            mgr = getattr(self.app, idmgr_name)
            sid = mgr._getNewToken()
            app = aq_base(self.app)
            thread = ReaderThread(sid, app, readiters, sdm_name, rlock)
            readers.append(thread)
        for i in range(numwriters):
            mgr = getattr(self.app, idmgr_name)
            sid = mgr._getNewToken()
            app = aq_base(self.app)
            thread = WriterThread(sid, app, writeiters, sdm_name, rlock)
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
        #rlock = threading.Lock()
        rlock = DumboLock()
        sdm_name = 'session_data_manager'
        mgr = getattr(self.app, idmgr_name)
        sid = mgr._getNewToken()
        for i in range(numreaders):
            app = aq_base(self.app)
            thread = ReaderThread(sid, app, readiters, sdm_name, rlock)
            readers.append(thread)
        for i in range(numwriters):
            app = aq_base(self.app)
            thread = WriterThread(sid, app, writeiters, sdm_name, rlock)
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

class ReaderThread(threading.Thread):
    def __init__(self, sid, app, iters, sdm_name, rlock):
        self.sid = sid
        self.conn, self.app = _openApp()
        self.iters = iters
        self.sdm_name = sdm_name
        self.out = []
        self.rlock = rlock
        #print "Reader SID %s" % sid
        threading.Thread.__init__(self)

    def run1(self):
        try:
            self.rlock.acquire("Reader 1")
            self.app = self.conn.root()['Application']
            self.app = makerequest.makerequest(self.app)
            self.app.REQUEST.session_token_ = self.sid
            session_data_manager = getattr(self.app, self.sdm_name)
            data = session_data_manager.getSessionData(create=1)
            t = time.time()
            data[t] = 1
            get_transaction().commit()
            self.rlock.release("Reader 1")
            for i in range(self.iters):
                self.rlock.acquire("Reader 2")
                try:
                    data = session_data_manager.getSessionData()
                except KeyError:  # Ugh
                    raise ConflictError
                if not data.has_key(t): self.out.append(1)
                self.rlock.release("Reader 2")
                time.sleep(whrandom.choice(range(3)))
                self.rlock.acquire("Reader 3")
                get_transaction().commit()
                self.rlock.release("Reader 3")
        finally:
            self.rlock.release("Reader catchall")
            try:
                self.conn.close()
            except AttributeError: pass     # ugh

    def run(self):

        i = 0

        while 1: 
            try:
                self.run1()
                return
            except ConflictError:
                i = i + 1
                #print "conflict %d" % i
                if i > 3: raise
                pass
            
class WriterThread(threading.Thread):
    def __init__(self, sid, app, iters, sdm_name, rlock):
        self.sid = sid
        self.conn, self.app = _openApp()
        self.iters = iters
        self.sdm_name = sdm_name
        self.rlock = rlock
        #print "Writer SID %s" % sid
        threading.Thread.__init__(self)

    def run1(self):
        try:
            self.rlock.acquire("Writer 1")
            self.app = self.conn.root()['Application']
            self.app = makerequest.makerequest(self.app)
            self.app.REQUEST.session_token_ = self.sid
            session_data_manager = getattr(self.app, self.sdm_name)
            self.rlock.release("Writer 1")
            for i in range(self.iters):
                self.rlock.acquire("Writer 2")
                try:
                    data = session_data_manager.getSessionData()
                except KeyError:  # Ugh
                    raise ConflictError
                data[time.time()] = 1
                n = whrandom.choice(range(8))
                self.rlock.release("Writer 2")
                time.sleep(n)
                self.rlock.acquire("Writer 3")
                if n % 2 == 0:
                    get_transaction().commit()
                else:
                    get_transaction().abort()
                self.rlock.release("Writer 3")
        finally:
            self.rlock.release("Writer Catchall")
            try:
                self.conn.close()
            except AttributeError: pass     # ugh

    def run(self):

        i = 0

        while 1: 
            try:
                self.run1()
                return
            except ConflictError:
                i = i + 1
                #print "conflict %d" % i
                if i > 3: raise
                pass
        

class DumboLock:
    def __init__(self):
        self.lock = threading.Lock()
        self._locked_ = 0
    def acquire(self, msg):
        #print "Acquiring lock %s" % msg
        #self.lock.acquire()
        #if self._locked_ == 1:
        #    print "already locked?!"
        self._locked_ = 1
    def release(self, msg):
        #print "Releasing lock %s" % msg
        #if self._locked_ == 0:
        #    print "already released?!"
        #    return
        #self.lock.release()
        self._locked_ = 0
                
def test_suite():
    test_datamgr = makeSuite(TestSessionManager, 'test')
    test_multithread = makeSuite(TestMultiThread, 'test')
    suite = TestSuite((test_datamgr, test_multithread))
    return suite

if __name__ == '__main__':
    runner = TextTestRunner(verbosity=9, descriptions=9)
    runner.run(test_suite())

