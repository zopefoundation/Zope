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

from Testing import makerequest
import ZODB
from ZODB.POSException import InvalidObjectReference, ConflictError
from Persistence import Persistent
from ZODB.DemoStorage import DemoStorage
import transaction
from OFS.DTMLMethod import DTMLMethod
import Acquisition
from Acquisition import aq_base
from Products.Sessions.BrowserIdManager import BrowserIdManager
from Products.Sessions.SessionDataManager import \
     SessionDataManager, SessionDataManagerErr, SessionDataManagerTraverser
from Products.Transience.Transience import \
     TransientObjectContainer, TransientObject
from Products.TemporaryFolder.TemporaryFolder import MountedTemporaryFolder
from DateTime import DateTime
from unittest import TestCase, TestSuite, TextTestRunner, makeSuite
import time, threading
from cPickle import UnpickleableError
from OFS.Application import Application
from ZPublisher.BeforeTraverse import registerBeforeTraverse, \
     unregisterBeforeTraverse

tf_name = 'temp_folder'
idmgr_name = 'browser_id_manager'
toc_name = 'temp_transient_container'
sdm_name = 'session_data_manager'

stuff = {}

def _getDB():
    db = stuff.get('db')
    if not db:
        ds = DemoStorage()
        db = ZODB.DB(ds, pool_size=60)
        conn = db.open()
        root = conn.root()
        app = Application()
        root['Application']= app
        transaction.savepoint(optimistic=True)
        _populate(app)
        stuff['db'] = db
        conn.close()
    return db

def _delDB():
    transaction.abort()
    del stuff['db']

class DummyAqImplicit(Acquisition.Implicit):
    pass

class DummyPersistent(Persistent):
    pass

def _populate(app):
    bidmgr = BrowserIdManager(idmgr_name)
    tf = MountedTemporaryFolder(tf_name, title="Temporary Folder")
    toc = TransientObjectContainer(toc_name, title='Temporary '
        'Transient Object Container', timeout_mins=20)
    session_data_manager=SessionDataManager(id=sdm_name,
        path='/'+tf_name+'/'+toc_name, title='Session Data Manager',
        requestName='TESTOFSESSION')

    try: app._delObject(idmgr_name)
    except (AttributeError, KeyError): pass

    try: app._delObject(tf_name)
    except (AttributeError, KeyError): pass

    try: app._delObject(sdm_name)
    except (AttributeError, KeyError): pass

    try: app._delObject('index_html')
    except (AttributeError, KeyError): pass

    app._setObject(idmgr_name, bidmgr)

    app._setObject(sdm_name, session_data_manager)

    app._setObject(tf_name, tf)
    transaction.commit()

    app.temp_folder._setObject(toc_name, toc)
    transaction.commit()

    # index_html necessary for publishing emulation for testAutoReqPopulate
    app._setObject('index_html', DTMLMethod('', __name__='foo'))
    transaction.commit()

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
        self.failUnless(self.app.session_data_manager.id == \
                        sdm_name)

    def testHasTitle(self):
        self.failUnless(self.app.session_data_manager.title \
                        == 'Session Data Manager')

    def testGetSessionDataNoCreate(self):
        sd = self.app.session_data_manager.getSessionData(0)
        self.failUnless(sd is None)

    def testGetSessionDataCreate(self):
        sd = self.app.session_data_manager.getSessionData(1)
        self.failUnless(sd.__class__ is TransientObject)

    def testHasSessionData(self):
        sd = self.app.session_data_manager.getSessionData()
        self.failUnless(self.app.session_data_manager.hasSessionData())

    def testNotHasSessionData(self):
        self.failUnless(not self.app.session_data_manager.hasSessionData())

    def testSessionDataWrappedInSDMandTOC(self):
        sd = self.app.session_data_manager.getSessionData(1)
        sdm = aq_base(getattr(self.app, sdm_name))
        toc = aq_base(getattr(self.app.temp_folder, toc_name))

        self.failUnless(aq_base(sd.aq_parent) is sdm)
        self.failUnless(aq_base(sd.aq_parent.aq_parent) is toc)

    def testNewSessionDataObjectIsValid(self):
        sdType = type(TransientObject(1))
        sd = self.app.session_data_manager.getSessionData()
        self.failUnless(type(aq_base(sd)) is sdType)
        self.failUnless(not hasattr(sd, '_invalid'))

    def testBrowserIdIsSet(self):
        sd = self.app.session_data_manager.getSessionData()
        mgr = getattr(self.app, idmgr_name)
        self.failUnless(mgr.hasBrowserId())

    def testGetSessionDataByKey(self):
        sd = self.app.session_data_manager.getSessionData()
        mgr = getattr(self.app, idmgr_name)
        token = mgr.getBrowserId()
        bykeysd = self.app.session_data_manager.getSessionDataByKey(token)
        self.failUnless(sd == bykeysd)

    def testBadExternalSDCPath(self):
        sdm = self.app.session_data_manager
        # fake out webdav
        sdm.REQUEST['REQUEST_METHOD'] = 'GET'
        sdm.setContainerPath('/fudgeffoloo')
        self.assertRaises(SessionDataManagerErr, self._testbadsdcpath)

    def _testbadsdcpath(self):
        self.app.session_data_manager.getSessionData()

    def testInvalidateSessionDataObject(self):
        sdm = self.app.session_data_manager
        sd = sdm.getSessionData()
        sd['test'] = 'Its alive!  Alive!'
        sd.invalidate()
        self.failUnless(not sdm.getSessionData().has_key('test'))

    def testGhostUnghostSessionManager(self):
        sdm = self.app.session_data_manager
        transaction.commit()
        sd = sdm.getSessionData()
        sd.set('foo', 'bar')
        sdm._p_changed = None
        transaction.commit()
        self.failUnless(sdm.getSessionData().get('foo') == 'bar')

    def testSubcommitAssignsPJar(self):
        sd = self.app.session_data_manager.getSessionData()
        dummy = DummyPersistent()
        sd.set('dp', dummy)
        self.failUnless(sd['dp']._p_jar is None)
        transaction.savepoint(optimistic=True)
        self.failIf(sd['dp']._p_jar is None)

    def testForeignObject(self):
        self.assertRaises(InvalidObjectReference, self._foreignAdd)

    def _foreignAdd(self):
        ob = self.app.session_data_manager

        # we don't want to fail due to an acquisition wrapper
        ob = ob.aq_base

        # we want to fail for some other reason:
        sd = self.app.session_data_manager.getSessionData()
        sd.set('foo', ob)
        transaction.commit()

    def testAqWrappedObjectsFail(self):
        a = DummyAqImplicit()
        b = DummyAqImplicit()
        aq_wrapped = a.__of__(b)
        sd = self.app.session_data_manager.getSessionData()
        sd.set('foo', aq_wrapped)
        self.assertRaises(TypeError, transaction.commit)

    def testAutoReqPopulate(self):
        self.app.REQUEST['PARENTS'] = [self.app]
        self.app.REQUEST['URL'] = 'a'
        self.app.REQUEST.traverse('/')
        self.failUnless(self.app.REQUEST.has_key('TESTOFSESSION'))

    def testUnlazifyAutoPopulated(self):
        self.app.REQUEST['PARENTS'] = [self.app]
        self.app.REQUEST['URL'] = 'a'
        self.app.REQUEST.traverse('/')
        sess = self.app.REQUEST['TESTOFSESSION']
        sdType = type(TransientObject(1))
        self.failUnless(type(aq_base(sess)) is sdType)

def test_suite():
    test_datamgr = makeSuite(TestSessionManager, 'test')
    suite = TestSuite((test_datamgr,))
    return suite

if __name__ == '__main__':
    runner = TextTestRunner(verbosity=9, descriptions=9)
    runner.run(test_suite())
