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

__rcs_id__='$Id: testUserFolder.py,v 1.4 2001/11/28 15:50:52 matt Exp $'
__version__='$Revision: 1.4 $'[11:-2]

import os, sys, unittest

import ZODB
from DocumentTemplate import HTML
from DocumentTemplate.tests.testDTML import DTMLTests
from Products.PythonScripts.standard import DTML
from AccessControl import User, Unauthorized
from AccessControl.User import BasicUserFolder
from ExtensionClass import Base

class SecurityTests (DTMLTests):

    def testMaxListUsers(self):
        # create a folder-ish thing which contains a roleManager,
        # then put an acl_users object into the folde-ish thing

        class Folderish(BasicUserFolder):
            def __init__(self, size, count):
                self.maxlistusers = size
                self.users = []
                self.acl_users = self
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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( SecurityTests ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
