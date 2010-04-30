import ZODB # in order to get Persistence.Persistent working
import transaction
from Testing import makerequest
from Products.Transience.Transience import TransientObjectContainer
import Products.Transience.Transience
import Products.Transience.TransientObject
from unittest import TestCase, TestSuite, makeSuite
from ZODB.DemoStorage import DemoStorage
from OFS.Application import Application
import fauxtime
import time as oldtime

WRITEGRANULARITY = 30
stuff = {}

def _getApp():
    app = stuff.get('app', None)
    if not app:
        ds = DemoStorage()
        db = ZODB.DB(ds)
        conn = db.open()
        root = conn.root()
        app = Application()
        root['Application']= app
        transaction.commit()
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
    transaction.abort()
    stuff['conn'].close()
    del stuff['conn']
    del stuff['app']
    del stuff['db']


class TestBase(TestCase):
    def setUp(self):
        Products.Transience.Transience.time = fauxtime
        Products.Transience.TransientObject.time = fauxtime
        Products.Transience.Transience.setStrict(1)
        self.app = makerequest.makerequest(_getApp())
        timeout = self.timeout = 1
        sm=TransientObjectContainer(
            id='sm', timeout_mins=timeout, title='SessionThing',
            addNotification=addNotificationTarget,
            delNotification=delNotificationTarget)
        self.app._setObject('sm', sm)

    def tearDown(self):
        transaction.abort()
        _delApp()
        del self.app
        Products.Transience.Transience.time = oldtime
        Products.Transience.TransientObject.time = oldtime
        Products.Transience.Transience.setStrict(0)

class TestLastAccessed(TestBase):
    def testLastAccessed(self):
        sdo = self.app.sm.new_or_existing('TempObject')
        la1 = sdo.getLastAccessed()
        # time.time() on Windows has coarse granularity (updates at
        # 18.2 Hz -- about once each 0.055 seconds).  We have to sleep
        # long enough so that "the next" call to time.time() actually
        # delivers a larger value.  _last_accessed isn't actually updated
        # unless current time.time() is greater than the last value +
        # WRITEGRANULARITY.  The time() and sleep() are fudged by a
        # factor of 60, though.  The code here used to do
        #     fauxtime.sleep(WRITEGRANULARITY + 1)
        # and that wasn't enough on Windows.  The "+1" only added 1/60th
        # of a second sleep time in real time, much less than the Windows
        # time.time() resolution.  Rounding up 0.055 to 1 digit and
        # multiplying by 60 ensures that we'll actually sleep long enough
        # to get to the next Windows time.time() tick.
        fauxtime.sleep(WRITEGRANULARITY + 0.06 * 60)
        sdo = self.app.sm.get('TempObject')
        self.assert_(sdo.getLastAccessed() > la1)

class TestNotifications(TestBase):
    def testAddNotification(self):
        self.app.sm.setAddNotificationTarget(addNotificationTarget)
        sdo = self.app.sm.new_or_existing('TempObject')
        now = fauxtime.time()
        k = sdo.get('starttime')
        self.assertEqual(type(k), type(now))
        self.assert_(k <= now)

    def testDelNotification(self):
        self.app.sm.setDelNotificationTarget(delNotificationTarget)
        sdo = self.app.sm.new_or_existing('TempObject')
        # sleep longer than timeout
        fauxtime.sleep(self.timeout * 100.0)
        self.app.sm.get('TempObject')
        now = fauxtime.time()
        k = sdo.get('endtime')
        self.assertEqual(type(k), type(now))
        self.assert_(k <= now)

    def testMissingCallbackGetCallbackReturnsNone(self):
        # in response to http://zope.org/Collectors/Zope/1403
        self.assertEqual(None, self.app.sm._getCallback('/foo/bar/baz'))


def addNotificationTarget(item, context):
    item['starttime'] = fauxtime.time()


def delNotificationTarget(item, context):
    item['endtime'] = fauxtime.time()


def test_suite():
    last_accessed = makeSuite(TestLastAccessed, 'test')
    start_end = makeSuite(TestNotifications, 'test')
    suite = TestSuite((start_end, last_accessed))
    return suite
