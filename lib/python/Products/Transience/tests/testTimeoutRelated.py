import sys, os, time, unittest

if __name__=='__main__':
    sys.path.insert(0, '..')
    sys.path.insert(0, '../../..')
    #os.chdir('../../..')

import ZODB # in order to get Persistence.Persistent working
from Testing import makerequest
import Acquisition
from Acquisition import aq_base
from Products.Transience.Transience import TransientObjectContainer
from Products.Transience.Transience import WRITEGRANULARITY
import Products.Transience.Transience
from Products.PythonScripts.PythonScript import PythonScript
from ZODB.POSException import InvalidObjectReference
from DateTime import DateTime
from unittest import TestCase, TestSuite, TextTestRunner, makeSuite
import time, threading, whrandom

epoch = time.time()

class TestBase(TestCase):
    def setUp(self):
        import Zope

        Products.Transience.Transience.time = fauxtime

        self.app = makerequest.makerequest(Zope.app())

        del Zope

        timeout = self.timeout = 1

        sm=TransientObjectContainer(
            id='sm', timeout_mins=timeout, title='SessionThing',
            addNotification=addNotificationTarget,
            delNotification=delNotificationTarget)

        self.app._setObject('sm', sm)

    def tearDown(self):
        get_transaction().abort()
        self.app._p_jar.close()
        self.app = None
        del self.app

class TestLastAccessed(TestBase):
    def testLastAccessed(self):

        sdo = self.app.sm.new_or_existing('TempObject')

        la1 = sdo.getLastAccessed()

        fauxsleep(WRITEGRANULARITY + 1)

        sdo = self.app.sm['TempObject']

        assert sdo.getLastAccessed() > la1

class TestNotifications(TestBase):
    def testAddNotification(self):
        self.app.sm.setAddNotificationTarget(addNotificationTarget)
        sdo = self.app.sm.new_or_existing('TempObject')
        now = fauxtime()
        k = sdo.get('starttime')
        assert type(k) == type(now)
        assert k <= now

    def testDelNotification(self):
        self.app.sm.setDelNotificationTarget(delNotificationTarget)
        sdo = self.app.sm.new_or_existing('TempObject')
        timeout = self.timeout * 60
        fauxsleep(timeout + (timeout * .33))
        try:
            sdo1 = self.app.sm['TempObject']
        except KeyError: pass
        now = fauxtime()
        k = sdo.get('endtime')
        assert type(k) == type(now)
        assert k <= now

def addNotificationTarget(item, context):
    #print "addNotificationTarget called for %s" % item
    item['starttime'] = fauxtime()

def delNotificationTarget(item, context):
    #print "delNotificationTarget called for %s" % item
    item['endtime'] = fauxtime()

def fauxtime():
    """ False timer -- returns time 10 x faster than normal time """
    return (time.time() - epoch) * 10.0

def fauxsleep(duration):
    """ False sleep -- sleep for 1/10 the time specifed """
    time.sleep(duration / 10.0)

def test_suite():
    last_accessed = makeSuite(TestLastAccessed, 'test')
    start_end = makeSuite(TestNotifications, 'test')
    runner = TextTestRunner()
    suite = TestSuite((start_end, last_accessed))
    return suite

if __name__ == '__main__':
    runner = TextTestRunner(sys.stdout)
    runner.run(test_suite())
