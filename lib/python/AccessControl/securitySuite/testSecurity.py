#!/usr/bin/env python2.1

import os, sys
execfile(os.path.join(sys.path[0],'framework.py'))

import unittest,re
import Zope,ZPublisher,cStringIO
from OFS.Folder import Folder
from OFS.SimpleItem  import SimpleItem
from AccessControl import ClassSecurityInfo
from Acquisition import Implicit
import Globals

class TestObject(SimpleItem,Implicit):
    """ test object """

    security = ClassSecurityInfo()

    def __init__(self,id,marker):
        self.id = id
        self.marker=marker

    security.declarePrivate("private_func")
    def private_func(self):
        """ private func """
        return "i am private"


    security.declareProtected("Protect Permission","protected_func")
    def protected_func(self):
        """ proteced func """
        return "i am protected "


    security.declarePublic("public_func")
    def public_func(self):
        """ public func """
        return "i am public"


Globals.InitializeClass(TestObject)


class TestFolder(Folder,Implicit):
    """ test class """

    security = ClassSecurityInfo()
    security.declareObjectPrivate()

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

        if 'folder1' in self.root.objectIds():
            self.root._delObject('folder1') 

        if 'object1' in self.root.objectIds():
            self.root._delObject('object1') 
        
        f = TestFolder('folder1')
        self.root._setObject('folder1',f)

        f = TestFolder('folder2')
        self.root.folder1._setObject('folder2',f)

        obj = TestObject('object1','m1')
        self.root.folder1._setObject('object1',obj)

        obj = TestObject('looserObject','m1')
        self.root.folder1._setObject('looserObject',obj)


        obj = TestObject('object2','m2')
        self.root.folder1.folder2._setObject('object2',obj)
        print self.root.folder1.folder2.getOwner()
    
        get_transaction().commit()
    


    def testPublicFunc(self):
        """ testing PublicFunc"""

        path = "/folder1/object1/public_func" 

        for user in USERS:
            code,txt= self._request(path,u=user.auth())
            assert code==200, (path,user,code,txt)

    def testPublicFuncWithWrongAuth(self):
        """ testing PublicFunc"""

        path = "/folder1/object1/public_func" 

        for user in USERS:
            code,txt= self._request(path,u=user.auth()+'xx')
            assert code==200, (path,user,code,txt)


    def testPrivateFunc(self):
        """ testing PrivateFunc"""

        path = "/folder1/object1/private_func" 

        for user in USERS:
            code,txt= self._request(path,u=user.auth())
            assert code==401, (path,user,code,txt)


    def testProtectedFunc(self):
        """ testing PrivateFunc"""

        path = "/folder1/object1/protected_func" 

        for user in USERS:
            code,txt= self._request(path,u=user.auth())

            if 'Manager' in user.roles:
                assert code==200, (path,user,code,txt)
            else:
                assert code==401, (path,user,code,txt)



    def testXX(self):
        """ xxx """
        for id,obj in self.root.objectItems():
            print id,obj.getOwner()


    def _request(self,*args,**kw):

        reg = re.compile("Status: ([0-9]{1,4}) (.*)",re.I)\

        io =cStringIO.StringIO()
        kw['s']=io
        ZPublisher.Zope(*args,**kw)
        outp = io.getvalue()
        mo = reg.search(outp)

        code,txt = mo.groups()

#        print "%-40s  %-20s   %3d %s" % (args[0],kw.get('u',''),int(code),txt)
        return int(code),txt
        
        
framework()

