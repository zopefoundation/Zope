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

# $Id$

import unittest

from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.User import nobody
from AccessControl.securitySuite import SecurityBase
from OFS.Folder import Folder
from OFS.SimpleItem  import SimpleItem
from App.class_init import InitializeClass


# let's define some permissions first

MAGIC_PERMISSION1 = 'Magic Permission 1'
MAGIC_PERMISSION2 = 'Magic Permission 2'


##############################################################################
# TestObject class
##############################################################################

class TestObject(SimpleItem):
    """ test object """

    security = ClassSecurityInfo()
    __allow_access_to_unprotected_subobjects__ = 0

    public_attr     = 1
    _protected_attr = 2

    def __init__(self,id):
        self.id = id

    security.declarePrivate("private_func")
    def private_func(self):
        """ private func """
        return "i am private"


    def manage_func(self):
        """ should be protected by manager role """
        return "i am your manager function"


    security.declareProtected(MAGIC_PERMISSION2,"manage_func2")
    def manage_func2(self):
        """ should be protected by manager role """
        return "i am your manager function2"


    security.declareProtected(MAGIC_PERMISSION1,"protected_func")
    def protected_func(self):
        """ proteced func """
        return "i am protected "


    security.declarePublic("public_func")
    def public_func(self):
        """ public func """
        return "i am public"

    security.setPermissionDefault(MAGIC_PERMISSION1, ("Manager","Owner"))
    security.setPermissionDefault(MAGIC_PERMISSION2, ("TestRole",))

InitializeClass(TestObject)


##############################################################################
# Testfolder class
##############################################################################

class TestFolder(Folder):
    """ test class """

    def __init__(self,id):
        self.id = id


    def getId(self): return self.id

    meta_type = 'TestFolder'

    security = ClassSecurityInfo()

InitializeClass(TestFolder)


##############################################################################
# User Class
##############################################################################

class User:

    def __init__(self,username,password,roles):
        self.username = username
        self.password = password
        self.roles    = roles

    def auth(self):
        return "%s:%s" % (self.username,self.password)


    def __str__(self):
        return "User(%s:%s:%s)" % (self.username,self.password,self.roles)

    __repr__ = __str__


USERS = (
    User('user1','123',[]),
    User('user2','123',[]),
    User('owner','123',('Owner',)),
    User('manager','123',('Manager',))
)

def getAuth(username):

    for user in USERS:
        if user.username==username:
            return "%s:%s" % (user.username,user.password)

    raise KeyError,"no such username: %" % username


class AVeryBasicSecurityTest(SecurityBase.SecurityBase):

    ################################################################
    # set up the test hierachy of objects
    ################################################################

    def setUp(self):
        """ my setup """

        self.root = SecurityBase.app
        acl = self.root.acl_users

        for user in USERS:
            try: acl._delUsers( user.username )
            except: pass

        for user in USERS:
            acl._addUser(user.username,user.password,user.password,
                            user.roles, [])

        # try to remove old crap

        if 'test' in self.root.objectIds():
            self.root._delObject('test')

        # setup Folder hierarchy

        test     = TestFolder('test')
        f1       = TestFolder('f1')
        f2       = TestFolder('f2')
        f3       = TestFolder('f3')
        obj      = TestObject('obj3')
        anonobj  = TestObject('anonobj')
        anonobj.__roles__ = ('Anonymous',)

        self.root._setObject('test',test)
        self.root.test._setObject('f1',f1)
        self.root.test._setObject('f2',f2)
        self.root.test.f1._setObject('anonobj',anonobj)
        self.root.test.f2._setObject('f3',f3)
        self.root.test.f2.f3._setObject('obj3',obj)


    def testNobody(self):
        """ check permissions for nobody user """

        self._checkPermission(nobody,'test.f1',   'View',1)
        self._checkPermission(nobody,'test.f2',   'View',1)
        self._checkPermission(nobody,'test.f2.f3','View',1)
        self._checkPermission(nobody,'test.f1',   MAGIC_PERMISSION1, None)
        self._checkPermission(nobody,'test.f2',   MAGIC_PERMISSION1, None)
        self._checkPermission(nobody,'test.f2.f3',MAGIC_PERMISSION1, None)


    def testPermissionAccess(self):
        """ check permission based access """

        self._checkRoles('test.f2.f3.obj3.public_func',     None)
        self._checkRoles('test.f2.f3.obj3.protected_func',  ('Manager','Owner'))
        self._checkRoles('test.f2.f3.obj3.manage_func',     ('Manager',))
        self._checkRoles('test.f2.f3.obj3.private_func',    ())


    def testZPublisherAccess(self):
        """ test access through ZPublisher """

        _r = [
               ('/test/f1/',                        None,    200),
               ('/test/f2',                         None,    200),
               ('/test/f2/f3',                      None,    200),
               ('/test/f2/f3/obj3/public_func',     None,    200),
               ('/test/f2/f3/obj3/protected_func',  None,    401),
               ('/test/f2/f3/obj3/manage_func',     None,    401),
               ('/test/f2/f3/obj3/private_func',    None,    401),

               ('/test/f1/',                        getAuth('manager'),    200),
               ('/test/f2',                         getAuth('manager'),    200),
               ('/test/f2/f3',                      getAuth('manager'),    200),
               ('/test/f2/f3/obj3/public_func',     getAuth('manager'),    200),
               ('/test/f2/f3/obj3/protected_func',  getAuth('manager'),    200),
               ('/test/f2/f3/obj3/manage_func',     getAuth('manager'),    200),
               ('/test/f2/f3/obj3/private_func',    getAuth('manager'),    401),

               ('/test/f1/',                        getAuth('owner'),    200),
               ('/test/f2',                         getAuth('owner'),    200),
               ('/test/f2/f3',                      getAuth('owner'),    200),
               ('/test/f2/f3/obj3/public_func',     getAuth('owner'),    200),
               ('/test/f2/f3/obj3/protected_func',  getAuth('owner'),    200),
               ('/test/f2/f3/obj3/manage_func',     getAuth('owner'),    401),
               ('/test/f2/f3/obj3/private_func',    getAuth('owner'),    401),

              ]

        for path,auth,expected in _r:
            if auth:
                res = self._checkRequest(path,u=auth,expected=expected)
            else:
                res = self._checkRequest(path,expected=expected)


def test_suite():
    return unittest.makeSuite(AVeryBasicSecurityTest)


def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
