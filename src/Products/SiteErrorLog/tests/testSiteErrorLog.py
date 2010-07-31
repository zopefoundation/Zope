"""SiteErrorLog tests
"""

from Testing.makerequest import makerequest

import Zope2
Zope2.startup()

import transaction

import sys
import unittest
import logging


class SiteErrorLogTests(unittest.TestCase):

    def setUp(self):
        transaction.begin()
        self.app = makerequest(Zope2.app())
        try:
            if not hasattr(self.app, 'error_log'):
                # If ZopeLite was imported, we have no default error_log
                from Products.SiteErrorLog.SiteErrorLog import SiteErrorLog
                self.app._setObject('error_log', SiteErrorLog())
            self.app.manage_addDTMLMethod('doc', '')
            
            self.logger = logging.getLogger('Zope.SiteErrorLog')
            self.log = logging.handlers.BufferingHandler(sys.maxint)
            self.logger.addHandler(self.log)
            self.old_level = self.logger.level
            self.logger.setLevel(logging.ERROR)
        except:
            self.tearDown()

    def tearDown(self):
        self.logger.removeHandler(self.log)
        self.logger.setLevel(self.old_level)
        transaction.abort()
        self.app._p_jar.close()

    def testInstantiation(self):
        # Retrieve the error_log by ID
        sel_ob = getattr(self.app, 'error_log', None)

        # Does the error log exist?
        self.assert_(sel_ob is not None)

        # Is the __error_log__ hook in place?
        self.assert_(self.app.__error_log__ == sel_ob)

        # Right now there should not be any entries in the log
        # but if another test fails and leaves something in the
        # log (which belongs to app , we get a spurious error here.
        # There's no real point in testing this anyway.
        #self.assertEquals(len(sel_ob.getLogEntries()), 0)

    def testSimpleException(self):
        # Grab the Site Error Log and make sure it's empty
        sel_ob = self.app.error_log
        previous_log_length = len(sel_ob.getLogEntries())

        # Fill the DTML method at self.root.doc with bogus code
        dmeth = self.app.doc
        dmeth.manage_upload(file="""<dtml-var expr="1/0">""")

        # "Faking out" the automatic involvement of the Site Error Log
        # by manually calling the method "raising" that gets invoked
        # automatically in a normal web request environment.
        try:
            dmeth.__call__()
        except ZeroDivisionError:
            sel_ob.raising(sys.exc_info())

        # Now look at the SiteErrorLog, it has one more log entry
        self.assertEquals(len(sel_ob.getLogEntries()), previous_log_length+1)

    def testForgetException(self):
        elog = self.app.error_log


        # Create a predictable error
        try:
            raise AttributeError, "DummyAttribute"
        except AttributeError:
            info = sys.exc_info()
            elog.raising(info)
        previous_log_length = len(elog.getLogEntries())

        entries = elog.getLogEntries()
        self.assertEquals(entries[0]['value'], "DummyAttribute")

        # Kick it
        elog.forgetEntry(entries[0]['id'])

        # Really gone?
        self.assertEquals(len(elog.getLogEntries()), previous_log_length-1)

    def testIgnoredException(self):
        # Grab the Site Error Log
        sel_ob = self.app.error_log
        previous_log_length = len(sel_ob.getLogEntries())

        # Tell the SiteErrorLog to ignore ZeroDivisionErrors
        current_props = sel_ob.getProperties()
        ignored = list(current_props['ignored_exceptions'])
        ignored.append('ZeroDivisionError')
        sel_ob.setProperties( current_props['keep_entries']
                            , copy_to_zlog = current_props['copy_to_zlog']
                            , ignored_exceptions = ignored
                            )

        # Fill the DTML method at self.root.doc with bogus code
        dmeth = self.app.doc
        dmeth.manage_upload(file="""<dtml-var expr="1/0">""")

        # "Faking out" the automatic involvement of the Site Error Log
        # by manually calling the method "raising" that gets invoked
        # automatically in a normal web request environment.
        try:
            dmeth.__call__()
        except ZeroDivisionError:
            sel_ob.raising(sys.exc_info())

        # Now look at the SiteErrorLog, it must have the same number of 
        # log entries
        self.assertEquals(len(sel_ob.getLogEntries()), previous_log_length)

    def testEntryID(self):
        elog = self.app.error_log

        # Create a predictable error
        try:
            raise AttributeError, "DummyAttribute"
        except AttributeError:
            info = sys.exc_info()
            elog.raising(info)

        entries = elog.getLogEntries()
        entry_id = entries[0]['id']

        self.assertTrue(entry_id in self.log.buffer[-1].msg, 
                        (entry_id, self.log.buffer[-1].msg))

    def testCleanup(self):
        # Need to make sure that the __error_log__ hook gets cleaned up
        self.app._delObject('error_log')
        self.assertEquals(getattr(self.app, '__error_log__', None), None)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SiteErrorLogTests))
    return suite
