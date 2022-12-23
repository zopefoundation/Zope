import os
import shutil
import tempfile
import time
import unittest

import transaction
import ZODB
import Zope2
from OFS.Application import Application
from OFS.History import Historical
from OFS.History import TemporalParadox
from OFS.SimpleItem import SimpleItem
from Testing.makerequest import makerequest
from ZODB.FileStorage import FileStorage


Zope2.startup_wsgi()


class HistoryItem(SimpleItem, Historical):
    pass


class HistoryTests(unittest.TestCase):
    def _getTargetClass(self):
        return HistoryItem

    def setUp(self):
        # set up a zodb
        # we can't use DemoStorage here 'cos it doesn't support History
        self.dir = tempfile.mkdtemp()
        fs_path = os.path.join(self.dir, 'testHistory.fs')
        self.s = FileStorage(fs_path, create=True)
        self.connection = ZODB.DB(self.s).open()
        r = self.connection.root()
        a = Application()
        r['Application'] = a
        self.root = makerequest(a)
        # create a history item object
        self.root['test'] = self._getTargetClass()()
        self.hi = hi = self.root.test
        # commit some changes
        hi.title = 'First title'
        t = transaction.get()
        # undo note made by Application instantiation above.
        t.description = None
        t.note('Change 1')
        t.commit()
        time.sleep(0.02)  # wait at least one Windows clock tick
        hi.title = 'Second title'
        t = transaction.get()
        t.note('Change 2')
        t.commit()
        time.sleep(0.02)  # wait at least one Windows clock tick
        hi.title = 'Third title'
        t = transaction.get()
        t.note('Change 3')
        t.commit()

    def tearDown(self):
        # get rid of ZODB
        transaction.abort()
        self.connection.close()
        self.s.close()
        del self.root
        del self.connection
        del self.s
        shutil.rmtree(self.dir)

    def test_manage_change_history(self):
        r = self.hi.manage_change_history()
        self.assertEqual(len(r), 3)  # three transactions
        for i in range(3):
            entry = r[i]
            # check no new keys show up without testing
            self.assertEqual(len(entry.keys()), 6)
            # the transactions are in newest-first order
            self.assertEqual(entry['description'], 'Change %i' % (3 - i))
            self.assertTrue('key' in entry)
            # lets not assume the size will stay the same forever
            self.assertTrue('size' in entry)
            self.assertTrue('tid' in entry)
            self.assertTrue('time' in entry)
            if i:
                # check times are increasing
                self.assertTrue(entry['time'] < r[i - 1]['time'])
            self.assertEqual(entry['user_name'], '')

    def test_manage_historyCopy(self):
        # we assume this works 'cos it's tested above
        r = self.hi.manage_change_history()
        # now we do the copy
        self.hi.manage_historyCopy(keys=[r[2]['key']])
        # do a commit, just like ZPublisher would
        transaction.commit()
        # check the body is as it should be, we assume
        # (hopefully not foolishly)
        # that all other attributes will behave the same
        self.assertEqual(self.hi.title,
                         'First title')

    def test_HistoricalRevisions(self):
        r = self.hi.manage_change_history()
        historical_revision = self.hi.HistoricalRevisions[r[2]['key']]
        self.assertIsInstance(historical_revision, self._getTargetClass())
        self.assertEqual(historical_revision.title, 'First title')
        # do a commit, just like ZPublisher would
        transaction.commit()

    def test_HistoricalRevisions_edit_causes_TemporalParadox(self):
        r = self.hi.manage_change_history()
        historical_revision = self.hi.HistoricalRevisions[r[2]['key']]
        historical_revision.title = 'Changed'
        self.assertRaises(TemporalParadox, transaction.commit)

    def test_manage_historicalComparison(self):
        r = self.hi.manage_change_history()
        # compare two revisions
        self.assertIn(
            'This object does not provide comparison support.',
            self.hi.manage_historicalComparison(
                REQUEST=self.hi.REQUEST,
                keys=[r[1]['key'], r[2]['key']]))

        # compare a revision with latest
        self.assertIn(
            'This object does not provide comparison support.',
            self.hi.manage_historicalComparison(
                REQUEST=self.hi.REQUEST,
                keys=[r[2]['key']]))

        # do a commit, just like ZPublisher would
        transaction.commit()


class HistoryItemWithComparisonSupport(SimpleItem, Historical):
    def manage_historyCompare(self, rev1, rev2, REQUEST,
                              historyComparisonResults=''):
        return super().manage_historyCompare(
            rev1, rev2, REQUEST,
            historyComparisonResults=f'old: {rev1.title} new: {rev2.title}')


class HistoryWithComparisonSupportTests(HistoryTests):
    def _getTargetClass(self):
        return HistoryItemWithComparisonSupport

    def test_manage_historicalComparison(self):
        r = self.hi.manage_change_history()
        # compare two revisions
        self.assertIn(
            'old: First title new: Second title',
            self.hi.manage_historicalComparison(
                REQUEST=self.hi.REQUEST,
                keys=[r[1]['key'], r[2]['key']]))

        # compare a revision with latest
        self.assertIn(
            'old: First title new: Third title',
            self.hi.manage_historicalComparison(
                REQUEST=self.hi.REQUEST,
                keys=[r[2]['key']]))


class HistoryItemWithSetState(HistoryItem):
    """A class with a data migration on __setstate__
    """
    def __setstate__(self, state):
        super().__setstate__(state)
        self.changed_something = True


class HistoryWithSetStateTest(HistoryTests):
    def _getTargetClass(self):
        return HistoryItemWithSetState
