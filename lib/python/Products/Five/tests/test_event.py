##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test events triggered by Five

$Id: test_event.py 12915 2005-05-31 10:23:19Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Products.Five.tests.fivetest import *

import transaction

from Products.Five.tests.products.FiveTest.subscriber import clear
from Products.Five.tests.products.FiveTest.subscriber import objectEventCatcher, \
     objectAddedEventCatcher, objectMovedEventCatcher, \
     objectCopiedEventCatcher, objectRemovedEventCatcher

from Products.Five.tests.products.FiveTest.simplecontent import manage_addSimpleContent
from Products.Five.tests.products.FiveTest.helpers import manage_addNoVerifyPasteFolder


class EventTest(FiveTestCase):

    def afterSetUp(self):
        manage_addNoVerifyPasteFolder(self.folder, 'npvf')
        self.folder = self.folder.npvf

        uf = self.folder.acl_users
        uf._doAddUser('manager', 'r00t', ['Manager'], [])
        self.login('manager')
        self.setPermissions(
            standard_permissions + ['Copy or Move'], 'Manager')
        # clear all events
        clear()

    def test_added_event(self):
        manage_addSimpleContent(self.folder, 'foo', 'Foo')
        foo = self.folder.foo
        events = objectEventCatcher.getEvents()
        self.assertEquals(1, len(events))
        self.assertEquals(foo.getPhysicalPath(),
                          events[0].object.getPhysicalPath())
        events = objectAddedEventCatcher.getEvents()
        self.assertEquals(1, len(events))
        self.assertEquals(foo.getPhysicalPath(),
                          events[0].object.getPhysicalPath())
        self.assertEquals(foo.aq_parent.getPhysicalPath(),
                          events[0].newParent.getPhysicalPath())

    def test_moved_event(self):
        manage_addSimpleContent(self.folder, 'foo', 'Foo')
        # somehow we need to at least commit a subtransaction to make
        # renaming succeed
        transaction.savepoint()
        self.folder.manage_renameObject('foo', 'bar')
        bar = self.folder.bar
        events = objectEventCatcher.getEvents()
        self.assertEquals(3, len(events))
        # will have new location so should still match
        self.assertEquals(bar.getPhysicalPath(),
                          events[0].object.getPhysicalPath())
        self.assertEquals(bar.getPhysicalPath(),
                          events[1].object.getPhysicalPath())
        # removed event
        self.assertEquals('foo',
                          events[1].oldName)
        self.assertEquals(None,
                          events[1].newName)
        # moved event
        self.assertEquals('foo',
                          events[2].oldName)
        self.assertEquals('bar',
                          events[2].newName)
        self.assertEquals(self.folder.getPhysicalPath(),
                          events[2].oldParent.getPhysicalPath())
        self.assertEquals(self.folder.getPhysicalPath(),
                          events[2].oldParent.getPhysicalPath())

    def test_moved_event2(self):
        # move from one folder to another
        manage_addNoVerifyPasteFolder(self.folder, 'folder1', 'Folder1')
        folder1 = self.folder.folder1
        manage_addNoVerifyPasteFolder(self.folder, 'folder2', 'Folder2')
        folder2 = self.folder.folder2
        manage_addSimpleContent(folder1, 'foo', 'Foo')
        foo = folder1.foo
        # need to trigger subtransaction before copy/paste can work
        transaction.savepoint()
        cb = folder1.manage_cutObjects(['foo'])
        folder2.manage_pasteObjects(cb)
        newfoo = folder2.foo

        events = objectMovedEventCatcher.getEvents()
        self.assertEquals(3, len(events))
        self.assertEquals(1, len(objectAddedEventCatcher.getEvents()))
        # removed event
        self.assertEquals(folder1.getPhysicalPath(),
                          events[1].oldParent.getPhysicalPath())
        self.assertEquals(None,
                          events[1].newParent)
        # moved event
        self.assertEquals(newfoo.getPhysicalPath(),
                          events[2].object.getPhysicalPath())
        self.assertEquals(folder1.getPhysicalPath(),
                          events[2].oldParent.getPhysicalPath())
        self.assertEquals(folder2.getPhysicalPath(),
                          events[2].newParent.getPhysicalPath())
        self.assertEquals('foo',
                          events[2].oldName)
        self.assertEquals('foo',
                          events[2].newName)

    def test_copied_event(self):
        manage_addSimpleContent(self.folder, 'foo', 'Foo')
        manage_addNoVerifyPasteFolder(self.folder, 'folder1')
        folder1 = self.folder.folder1
        # need to trigger subtransaction before copy/paste can work
        transaction.savepoint()
        cb = self.folder.manage_copyObjects(['foo'])
        folder1.manage_pasteObjects(cb)
        foo_copy = folder1.foo
        events = objectCopiedEventCatcher.getEvents()
        self.assertEquals(1, len(events))
        self.assertEquals(foo_copy.getPhysicalPath(),
                          events[0].object.getPhysicalPath())
        events = objectAddedEventCatcher.getEvents()
        self.assertEquals(2, len(events))
        self.assertEquals(foo_copy.getPhysicalPath(),
                          events[1].object.getPhysicalPath())

    def test_removed_event(self):
        manage_addSimpleContent(self.folder, 'foo', 'Foo')
        self.folder.manage_delObjects(['foo'])
        events = objectRemovedEventCatcher.getEvents()
        self.assertEquals(1, len(events))
        self.assertEquals('foo', events[0].object.id)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(EventTest))
    return suite

if __name__ == '__main__':
    framework()

