##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import sys, os, time
if __name__ == "__main__":
    sys.path.insert(0, '../../..')
    #os.chdir('../../..')
from Testing import makerequest
import ZODB # in order to get Persistence.Persistent working
import transaction
import Acquisition
from Acquisition import aq_base
from Products.Sessions.BrowserIdManager import BrowserIdManager, \
     getNewBrowserId
from Products.Sessions.SessionDataManager import \
    SessionDataManager, SessionDataManagerErr
from Products.Transience.Transience import \
    TransientObjectContainer, TransientObject
from Products.TemporaryFolder.TemporaryFolder import MountedTemporaryFolder
from Products.TemporaryFolder.LowConflictConnection import \
     LowConflictConnection
from ZODB.Connection import Connection
from ZODB.POSException import InvalidObjectReference, ConflictError, \
     ReadConflictError, BTreesConflictError
from DateTime import DateTime
from unittest import TestCase, TestSuite, TextTestRunner, makeSuite
import time, threading, random
from cPickle import UnpickleableError
from ZODB.DemoStorage import DemoStorage
from tempstorage.TemporaryStorage import TemporaryStorage
from OFS.Application import Application
from OFS.Folder import Folder
import sys
import time
import traceback
sys.setcheckinterval(200)

from Products.Transience.tests import fauxtime
import Products.Transience.Transience
import Products.Transience.TransientObject
Products.Transience.Transience.time = fauxtime
Products.Transience.TransientObject.time = fauxtime

tf_name = 'temp_folder'
idmgr_name = 'browser_id_manager'
toc_name = 'temp_transient_container'
sdm_name = 'session_data_manager'

stuff = {}

def log_time():
    """Return a simple time string without spaces suitable for logging."""
    return ("%4.4d-%2.2d-%2.2dT%2.2d:%2.2d:%2.2d"
            % time.localtime()[:6])


def _getDB():
    db = stuff.get('db')
    if not db:
        ds = DemoStorage()
        db = ZODB.DB(ds)
        conn = db.open()
        root = conn.root()
        app = Application()
        root['Application']= app
        _populate(app)
        transaction.commit()
        stuff['db'] = db
        conn.close()
    return db

def _delDB():
    transaction.abort()
    del stuff['db']

class Foo(Acquisition.Implicit): pass

def _populate(app):
    bidmgr = BrowserIdManager(idmgr_name)
    tf = MountedTemporaryFolder(tf_name, 'Temporary Folder')
    toc = TransientObjectContainer(toc_name, title='Temporary '
        'Transient Object Container', timeout_mins=1)
    session_data_manager=SessionDataManager(id=sdm_name,
        path='/'+tf_name+'/'+toc_name, title='Session Data Manager')

    try: app._delObject(idmgr_name)
    except AttributeError: pass

    try: app._delObject(tf_name)
    except AttributeError: pass

    try: app._delObject(sdm_name)
    except AttributeError: pass

    app._setObject(idmgr_name, bidmgr)

    app._setObject(sdm_name, session_data_manager)

    app._setObject(tf_name, tf)
    transaction.commit()

    app.temp_folder._setObject(toc_name, toc)
    transaction.commit()

class TestMultiThread(TestCase):
    def testOverlappingBrowserIds(self):
        token = getNewBrowserId()
        self.go(token)

    def testNonOverlappingBrowserIds(self):
        token = None
        self.go(token)

    def go(self, token):
        readers = []
        writers = []
        valuers = []
        readiters = 3
        writeiters = 3
        valueiters = 3
        numreaders = 2
        numwriters = 4
        numvaluers = 1
        db = _getDB()
        for i in range(numreaders):
            thread = ReaderThread(db, readiters, token)
            readers.append(thread)
        for i in range(numvaluers):
            thread = ValuesGetterThread(db, valueiters, token)
            valuers.append(thread)
        for i in range(numwriters):
            thread = WriterThread(db, writeiters, token)
            writers.append(thread)
        for thread in readers:
            thread.start()
            time.sleep(0.1)
        for thread in writers:
            thread.start()
            time.sleep(0.1)
        for thread in valuers:
            thread.start()
            time.sleep(0.1)
        active = threading.activeCount()
        while active > 0:
            active = threading.activeCount()-1
            print 'waiting for %s threads' % active
            print "readers: ", numActive(readers),
            print "writers: ", numActive(writers),
            print "valuers: ", numActive(valuers)
            time.sleep(5)

def numActive(threads):
    i = 0
    for thread in threads:
        if not thread.isFinished():
            i+=1
    return i

class BaseReaderWriter(threading.Thread):
    def __init__(self, db, iters, token=None):
        self.iters = iters
        self.sdm_name = sdm_name
        self.finished = 0
        self.db = db
        self.token = token
        threading.Thread.__init__(self)

    def run(self):
        i = 0
        try:
            while 1:
                self.conn = self.db.open()
                self.app = self.conn.root()['Application']
                self.app = makerequest.makerequest(self.app)
                if self.token is None:
                    token = getNewBrowserId()
                else:
                    token = self.token
                    self.app.REQUEST.browser_id_ = token

                try:
                    self.run1()
                    return
                except ReadConflictError:
                    #traceback.print_exc()
                    print "R",
                except BTreesConflictError:
                    print "B",
                except ConflictError:
                    print "W",
                except:
                    transaction.abort()
                    print log_time()
                    traceback.print_exc()
                    raise
                
                i = i + 1
                transaction.abort()
                self.conn.close()
                time.sleep(random.randrange(10) * .1)
        finally:
            transaction.abort()
            self.conn.close()
            del self.app
            self.finished = 1
            print '%s finished' % self.__class__

    def isFinished(self):
        return self.finished
        

class ReaderThread(BaseReaderWriter):
    def run1(self):
        session_data_manager = getattr(self.app, self.sdm_name)
        data = session_data_manager.getSessionData(create=1)
        t = time.time()
        data[t] = 1
        transaction.commit()
        for i in range(self.iters):
            data = session_data_manager.getSessionData()
            time.sleep(random.choice(range(3)))
            transaction.commit()

class WriterThread(BaseReaderWriter):
    def run1(self):
        session_data_manager = getattr(self.app, self.sdm_name)
        for i in range(self.iters):
            data = session_data_manager.getSessionData()
            data[time.time()] = 1
            n = random.choice(range(3))
            time.sleep(n)
            if n % 2 == 0:
                transaction.commit()
            else:
                transaction.abort()

class ValuesGetterThread(BaseReaderWriter):
    def run1(self):
        tf = getattr(self.app, tf_name)
        toc = getattr(tf, toc_name)
        for i in range(self.iters):
            print '%s values in toc' % len(toc.values())
            n = random.choice(range(3))
            time.sleep(n)
            if n % 2 == 0:
                transaction.commit()
            else:
                transaction.abort()


def test_suite():
    test_multithread = makeSuite(TestMultiThread, 'test')
    suite = TestSuite((test_multithread,))
    return suite

if __name__ == '__main__':
    runner = TextTestRunner(verbosity=9, descriptions=9)
    runner.run(test_suite())
