#!/usr/bin/env python2.1

import os, sys
execfile(os.path.join(sys.path[0],'framework.py'))

import unittest,re
import Zope,ZPublisher,cStringIO
from OFS.Folder import Folder
from OFS.SimpleItem  import SimpleItem
from OFS.DTMLMethod import addDTMLMethod
from AccessControl import ClassSecurityInfo,getSecurityManager
from AccessControl.User import nobody
import Globals

MAGIC_PERMISSION1 = 'Magic Permission 1'
MAGIC_PERMISSION2 = 'Magic Permission 2'


class TestObject(SimpleItem):
    """ test object """

    security = ClassSecurityInfo()
    __allow_access_to_unprotected_subobjects__ = 0

    attr1 = 1
    attr2 = 2

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

Globals.InitializeClass(TestObject)


class TestFolder(Folder):
    """ test class """

    def __init__(self,id):
        self.id = id
            

    def getId(self): return self.id 

    meta_type = 'TestFolder'

    security = ClassSecurityInfo()

Globals.InitializeClass(TestFolder)


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


class SecurityTests(unittest.TestCase) :

    def setUp(self):
        """ my setup """

        self.root = Zope.app()
        acl = self.root.acl_users

        for user in USERS:
            try: acl._delUsers( user.username )
            except: pass
   
        for user in USERS:
            acl._addUser(user.username,user.password,user.password,
                            user.roles, [])

        get_transaction().commit()

        # try to remove old crap

        if 'test' in self.root.objectIds():
            self.root._delObject('test') 

        # setup Folder hierarchy

        test = TestFolder('test')
        f1   = TestFolder('f1')
        f2   = TestFolder('f2')
        f3   = TestFolder('f3')
        obj  = TestObject('obj3')

        self.root._setObject('test',test)
        self.root.test._setObject('f1',f1)
        self.root.test._setObject('f2',f2)
        self.root.test.f2._setObject('f3',f3)
        self.root.test.f2.f3._setObject('obj3',obj)
        
        get_transaction().commit()


    def _testHierarchy(self):
        """ print all test objects, permissions and roles """
        self._PrintTestEnvironment(root=self.root.test)


    def _PrintTestEnvironment(self,root):
        """ print recursive all objects """

        print '....'*len(root.getPhysicalPath()),root.getId()

        folderObjs = []

        for id,obj in root.objectItems():

            if obj.meta_type in ['Folder','TestFolder']:
                folderObjs.append(obj)

            else:                
                print '    '*(1+len(root.getPhysicalPath())),obj.getId(),
                print getattr(obj,"__roles__",(None,))

        for folder in folderObjs:
            self._PrintTestEnvironment(folder)


    def testAttributeAccess(self):
        """ check access to attributes """

        obj = self.root.test.f2.f3.obj3
        print obj.attr1
        print obj.attr2

        obj.attr1 = 'sux'
        obj.attr2 = 'sux'


    def testNobody(self):
        """ check permissions for nobody user """


        self._checkPermission(nobody,'f1',   'View',1) 
        self._checkPermission(nobody,'f2',   'View',1) 
        self._checkPermission(nobody,'f2.f3','View',1) 
        self._checkPermission(nobody,'f1',   MAGIC_PERMISSION1, None) 
        self._checkPermission(nobody,'f2',   MAGIC_PERMISSION1, None) 
        self._checkPermission(nobody,'f2.f3',MAGIC_PERMISSION1, None) 



    def _checkPermission(self, user, hier, perm, expected):
        """ low level permission check """

        s = "self.root.test.%s" % hier
        obj = eval(s)

        res = user.has_permission(perm,obj)

        if res != expected:        
            raise AssertionError, \
                self._perm_error(s,perm,res,expected)


    def _perm_error(self, obj , perm, res, expected):
        s = '' 
        s+=' Object: %s' % obj
        s+=', Permission: %s' % perm 
        s+=', has permission: %s' % res 
        s+=', expected: %s' % expected

        return s
        


    def testPermissionAccess(self):
        """ check permission based access """

        self._checkRoles('f2.f3.obj3.public_func',     (None,))    
        self._checkRoles('f2.f3.obj3.protected_func',  ('Manager','Owner'))    
        self._checkRoles('f2.f3.obj3.manage_func',     ('Manager',))    
        self._checkRoles('f2.f3.obj3.private_func',    ('Manager',))    


    def _checkRoles(self,hier,expected_roles=()):
        
        s = "self.root.test.%s.__roles__" % hier
        roles = eval(s)

        if roles==None or len(roles)==0: 
            roles=(None,)
    
        self._debug(s,expected_roles,roles)

        for r in roles:
            assert r in expected_roles, (roles,expected_roles)
            

    def _debug(self,hier,expected_roles,got_roles):
        print '-'*78
        print 'Object:',hier
        print "has roles:",got_roles        
        print "expected roles:", expected_roles
        
        
framework()

