##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""User folder tests
"""

__rcs_id__='$Id: testUserFolder.py,v 1.7 2003/01/21 02:58:58 chrism Exp $'
__version__='$Revision: 1.7 $'[11:-2]

import os, sys, unittest

import ZODB
from AccessControl import User, Unauthorized
from AccessControl.User import BasicUserFolder, UserFolder, User
from ExtensionClass import Base

class UserFolderTests(unittest.TestCase):

    def testMaxListUsers(self):
        # create a folder-ish thing which contains a roleManager,
        # then put an acl_users object into the folde-ish thing

        class Folderish(BasicUserFolder):
            def __init__(self, size, count):
                self.maxlistusers = size
                self.users = []
                self.acl_users = self
                self.__allow_groups__ = self
                for i in xrange(count):
                    self.users.append("Nobody")

            def getUsers(self):
                return self.users

            def user_names(self):
                return self.getUsers()


        tinyFolderOver = Folderish(15, 20)
        tinyFolderUnder = Folderish(15, 10)

        assert tinyFolderOver.maxlistusers == 15
        assert tinyFolderUnder.maxlistusers == 15
        assert len(tinyFolderOver.user_names()) == 20
        assert len(tinyFolderUnder.user_names()) == 10

        try:
            list = tinyFolderOver.get_valid_userids()
            assert 0, "Did not raise overflow error"
        except OverflowError:
            pass

        try:
            list = tinyFolderUnder.get_valid_userids()
            pass
        except OverflowError:
            assert 0, "Raised overflow error erroneously"

class UserTests(unittest.TestCase):

    def testGetUserName(self):
        f = User('chris', '123', ['Manager'], [])
        self.assertEqual(f.getUserName(), 'chris')
        
    def testGetUserId(self):
        f = User('chris', '123', ['Manager'], [])
        self.assertEqual(f.getId(), 'chris')

    def testBaseUserGetIdEqualGetName(self):
        # this is true for the default user type, but will not
        # always be true for extended user types going forward (post-2.6)
        f = User('chris', '123', ['Manager'], [])
        self.assertEqual(f.getId(), f.getUserName())

    def testGetPassword(self):
        f = User('chris', '123', ['Manager'], [])
        self.assertEqual(f._getPassword(), '123')

    def testGetRoles(self):
        f = User('chris', '123', ['Manager'], [])
        self.assertEqual(f.getRoles(), ('Manager', 'Authenticated'))

    def testGetDomains(self):
        f = User('chris', '123', ['Manager'], [])
        self.assertEqual(f.getDomains(), ())

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UserFolderTests))
    suite.addTest(unittest.makeSuite(UserTests))
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
