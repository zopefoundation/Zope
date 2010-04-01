# vim: ts=4 expandtab :
##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import unittest
from Testing import ZopeTestCase

class TestRecursiveChangeOwnership(ZopeTestCase.ZopeTestCase):
    user_name2 = "dumdidum"
    user_pass2 = "dumdidum"

    def afterSetUp(self):

        # need a second user
        ufld = self.folder['acl_users']
        ufld.userFolderAddUser(self.user_name2, self.user_pass2, [], [])

        # remember user objects
        # is the __of__() call correct? is it needed? without it ownerInfo in
        # Owned.py throws an AttributeError ...
        self.user1 = self.folder['acl_users'].getUser(ZopeTestCase.user_name
                                                     ).__of__(self.folder)
        self.user2 = self.folder['acl_users'].getUser(self.user_name2
                                                     ).__of__(self.folder)

        self.folder.changeOwnership(self.user1)

        # need some objects owned by second user
        # beneath self.folder
        self.folder.manage_addFile("testfile")
        self.file = self.folder["testfile"]
        self.file.changeOwnership(self.user2)

    def testRecursiveChangeOwnership(self):
        # ensure folder is owned by user1
        owner = self.folder.getOwnerTuple()[1]
        self.assertEqual(owner, ZopeTestCase.user_name)

        # ensure file is owned by user2
        owner = self.file.getOwnerTuple()[1]
        self.assertEqual(owner, self.user_name2)

        self.folder.changeOwnership(self.user1, recursive=1)

        # ensure file's ownership has changed now to user1
        owner = self.file.getOwnerTuple()[1]
        self.assertEqual(owner, ZopeTestCase.user_name)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestRecursiveChangeOwnership),
    ))
