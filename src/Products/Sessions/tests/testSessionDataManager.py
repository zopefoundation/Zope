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
import unittest

tf_name = 'temp_folder'
idmgr_name = 'browser_id_manager'
toc_name = 'temp_transient_container'
sdm_name = 'session_data_manager'

stuff = {}


def _getDB():
    from OFS.Application import Application
    import transaction
    db = stuff.get('db')
    if not db:
        from ZODB import DB
        from ZODB.DemoStorage import DemoStorage
        ds = DemoStorage()
        db = DB(ds, pool_size=60)
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
    import transaction
    transaction.abort()
    del stuff['db']


def _populate(app):
    from OFS.DTMLMethod import DTMLMethod
    from Products.Sessions.BrowserIdManager import BrowserIdManager
    from Products.Sessions.SessionDataManager import SessionDataManager
    from Products.TemporaryFolder.TemporaryFolder import MountedTemporaryFolder
    from Products.Transience.Transience import TransientObjectContainer
    import transaction
    bidmgr = BrowserIdManager(idmgr_name)
    tf = MountedTemporaryFolder(tf_name, title="Temporary Folder")
    toc = TransientObjectContainer(toc_name, title='Temporary '
        'Transient Object Container', timeout_mins=20)
    session_data_manager=SessionDataManager(id=sdm_name,
        path='/'+tf_name+'/'+toc_name, title='Session Data Manager',
        requestName='TESTOFSESSION')

    try:
        app._delObject(idmgr_name)
    except (AttributeError, KeyError):
        pass

    try:
        app._delObject(tf_name)
    except (AttributeError, KeyError):
        pass

    try:
        app._delObject(sdm_name)
    except (AttributeError, KeyError):
        pass

    try:
        app._delObject('index_html')
    except (AttributeError, KeyError):
        pass

    app._setObject(idmgr_name, bidmgr)

    app._setObject(sdm_name, session_data_manager)

    app._setObject(tf_name, tf)
    transaction.commit()

    app.temp_folder._setObject(toc_name, toc)
    transaction.commit()

    # index_html necessary for publishing emulation for testAutoReqPopulate
    app._setObject('index_html', DTMLMethod('', __name__='foo'))
    transaction.commit()


class TestSessionManager(unittest.TestCase):

    def setUp(self):
        from Testing import makerequest
        db = _getDB()
        conn = db.open()
        root = conn.root()
        self.app = makerequest.makerequest(root['Application'])
        timeout = self.timeout = 1

    def tearDown(self):
        _delDB()
        del self.app

    def testHasId(self):
        self.assertTrue(self.app.session_data_manager.id == \
                        sdm_name)

    def testHasTitle(self):
        self.assertTrue(self.app.session_data_manager.title \
                        == 'Session Data Manager')

    def testGetSessionDataNoCreate(self):
        sd = self.app.session_data_manager.getSessionData(0)
        self.assertTrue(sd is None)

    def testGetSessionDataCreate(self):
        from Products.Transience.Transience import TransientObject
        sd = self.app.session_data_manager.getSessionData(1)
        self.assertTrue(sd.__class__ is TransientObject)

    def testHasSessionData(self):
        sd = self.app.session_data_manager.getSessionData()
        self.assertTrue(self.app.session_data_manager.hasSessionData())

    def testNotHasSessionData(self):
        self.assertTrue(not self.app.session_data_manager.hasSessionData())

    def testSessionDataWrappedInSDMandTOC(self):
        from Acquisition import aq_base
        sd = self.app.session_data_manager.getSessionData(1)
        sdm = aq_base(getattr(self.app, sdm_name))
        toc = aq_base(getattr(self.app.temp_folder, toc_name))

        self.assertTrue(aq_base(sd.aq_parent) is sdm)
        self.assertTrue(aq_base(sd.aq_parent.aq_parent) is toc)

    def testNewSessionDataObjectIsValid(self):
        from Acquisition import aq_base
        from Products.Transience.Transience import TransientObject
        sdType = type(TransientObject(1))
        sd = self.app.session_data_manager.getSessionData()
        self.assertTrue(type(aq_base(sd)) is sdType)
        self.assertTrue(not hasattr(sd, '_invalid'))

    def testBrowserIdIsSet(self):
        sd = self.app.session_data_manager.getSessionData()
        mgr = getattr(self.app, idmgr_name)
        self.assertTrue(mgr.hasBrowserId())

    def testGetSessionDataByKey(self):
        sd = self.app.session_data_manager.getSessionData()
        mgr = getattr(self.app, idmgr_name)
        token = mgr.getBrowserId()
        bykeysd = self.app.session_data_manager.getSessionDataByKey(token)
        self.assertTrue(sd == bykeysd)

    def testBadExternalSDCPath(self):
        from Products.Sessions.SessionDataManager import SessionDataManagerErr
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
        self.assertTrue(not sdm.getSessionData().has_key('test'))

    def testGhostUnghostSessionManager(self):
        import transaction
        sdm = self.app.session_data_manager
        transaction.commit()
        sd = sdm.getSessionData()
        sd.set('foo', 'bar')
        sdm._p_changed = None
        transaction.commit()
        self.assertTrue(sdm.getSessionData().get('foo') == 'bar')

    def testSubcommitAssignsPJar(self):
        global DummyPersistent # so pickle can find it
        from Persistence import Persistent
        import transaction
        class DummyPersistent(Persistent):
            pass
        sd = self.app.session_data_manager.getSessionData()
        dummy = DummyPersistent()
        sd.set('dp', dummy)
        self.assertTrue(sd['dp']._p_jar is None)
        transaction.savepoint(optimistic=True)
        self.assertFalse(sd['dp']._p_jar is None)

    def testForeignObject(self):
        from ZODB.POSException import InvalidObjectReference
        self.assertRaises(InvalidObjectReference, self._foreignAdd)

    def _foreignAdd(self):
        import transaction
        ob = self.app.session_data_manager

        # we don't want to fail due to an acquisition wrapper
        ob = ob.aq_base

        # we want to fail for some other reason:
        sd = self.app.session_data_manager.getSessionData()
        sd.set('foo', ob)
        transaction.commit()

    def testAqWrappedObjectsFail(self):
        from Acquisition import Implicit
        import transaction

        class DummyAqImplicit(Implicit):
            pass
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
        self.assertTrue(self.app.REQUEST.has_key('TESTOFSESSION'))

    def testUnlazifyAutoPopulated(self):
        from Acquisition import aq_base
        from Products.Transience.Transience import TransientObject
        self.app.REQUEST['PARENTS'] = [self.app]
        self.app.REQUEST['URL'] = 'a'
        self.app.REQUEST.traverse('/')
        sess = self.app.REQUEST['TESTOFSESSION']
        sdType = type(TransientObject(1))
        self.assertTrue(type(aq_base(sess)) is sdType)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestSessionManager),
    ))
