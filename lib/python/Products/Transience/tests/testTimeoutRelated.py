import sys, os, time
sys.path.insert(0, '..')
sys.path.insert(0, '../../..')
os.chdir('../../..')

import ZODB # in order to get Persistence.Persistent working
from Testing import makerequest
import Acquisition
from Acquisition import aq_base
from Products.Transience.Transience import TransientObjectContainer
#from Products.CoreSessionTracking.SessionIdManager import SessionIdManager
#from Products.Transience.Transience import TransientObject
from Products.Transience.Transience import WRITEGRANULARITY
import Products.Transience.Transience
from Products.PythonScripts.PythonScript import PythonScript
from ZODB.POSException import InvalidObjectReference
from DateTime import DateTime
from unittest import TestCase, TestSuite, TextTestRunner, makeSuite
import time, threading, whrandom

#sessionidmgr = 'session_id_mgr'
epoch = time.time()

class TestBase(TestCase):
    def setUp(self):
        import Zope

        Products.Transience.Transience.time = fauxtime

        self.app = makerequest.makerequest(Zope.app())

        del Zope

        timeout = self.timeout = 1

        #sidmgr = SessionIdManager(sessionidmgr)

        sm=TransientObjectContainer(
            id='sm', timeout_mins=timeout, title='SessionThing',
            addNotification=onstartf, delNotification=onendf)

        #try: self.app._delObject(sessionidmgr)
        #except AttributeError: pass

        try: self.app._delObject('sm')
        except AttributeError: pass
        try: self.app._delObject('onstartf')
        except AttributeError: pass
        try: self.app_delObject('onendf')
        except AttributeError: pass

        #self.app._setObject(sessionidmgr, sidmgr)

        self.app._setObject('sm', sm)

        #onstartf = PythonScript('onstartf')
        #self.app._setObject('onstartf', onstartf)
        #onstartf.write('##parameters=sdo\nsdo["a"]=context.ZopeTime()')
        #onstartf._makeFunction()
        #onendf = PythonScript('onendf')
        #self.app._setObject('onendf', onendf)
        #onendf.write('##parameters=sdo\nsdo.demo()')
        #onendf._makeFunction()
##         admin = self.app.acl_users.getUser('admin')
##         if admin is None:
##             raise "Need to define an 'admin' user before running these tests"
##         admin = admin.__of__(self.app.acl_users)
##        self.app.sm.changeOwnership(admin)

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

class TestOnStartEnd(TestBase):
    def testOnStart(self):
        self.app.sm.setAddNotificationTarget(onstartf)
        sdo = self.app.sm.new_or_existing('TempObject')
        now = fauxtime()
        k = sdo.get('starttime')
        assert type(k) == type(now)
        assert k <= now

    def testOnEnd(self):
        self.app.sm.setDelNotificationTarget(onendf)
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

def onstartf(item, context):
    #print "onstartf called for %s" % item
    item['starttime'] = fauxtime()

def onendf(item, context):
    #print "onendf called for %s" % item
    item['endtime'] = fauxtime()

def fauxtime():
    """ False timer -- returns time 10 x faster than normal time """
    return (time.time() - epoch) * 10.0

def fauxsleep(duration):
    """ False sleep -- sleep for 1/10 the time specifed """
    time.sleep(duration / 10.0)

if __name__ == '__main__':
    last_accessed = makeSuite(TestLastAccessed, 'test')
    start_end = makeSuite(TestOnStartEnd, 'test')
    runner = TextTestRunner()
    suite = TestSuite((start_end, last_accessed))
    runner.run(suite)



