#!/usr/bin/env python2.1

import os, sys
execfile(os.path.join(sys.path[0],'framework.py'))

import unittest,re
import Zope,ZPublisher,cStringIO
from OFS.Folder import Folder
from OFS.SimpleItem  import SimpleItem
from OFS.DTMLDocument import DTMLDocument
from OFS.DTMLMethod import DTMLMethod
from AccessControl import ClassSecurityInfo
import Globals


class ResultObject:

    def __str__(self,expected=-1):
        s  = '\n'
        s+= '-'*78
        s+= "\nRequest: %s" % self.request
        s+= "\nUser: %s" % self.user
        s+= "\nExpected: %s" % expected + "  got: %s %s" % (self.code,self.return_text)
        s+= "\nOutput:"
        s+= self.output
        s+= "\n"

        return s
    
    __repr__ = __str__

    def __call__(self,expected=-1):
        return self.__str__(expected)
        
        

class TestObject(SimpleItem):
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


    security.declarePublic('dtmlProtected')
    security.declarePublic('dtmlPrivate')
    security.declarePublic('dtmlPublic')
    # Using os.getcwd() sux here !
    dtmlProtected = Globals.DTMLFile('dtmlProtected',os.getcwd()+'/dtml')
    dtmlPublic    = Globals.DTMLFile('dtmlPublic',os.getcwd()+'/dtml')
    dtmlPrivate   = Globals.DTMLFile('dtmlPublic',os.getcwd()+'/dtml')


Globals.InitializeClass(TestObject)


class TestFolder(Folder):
    """ test class """

    def __init__(self,id):
        self.id = id

    def getId(self): return self.id 


    meta_type = 'TestFolder'

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
    
        get_transaction().commit()


    def testPrintTestEnvironment(self):
        """ print all test objects, permissions and roles """
        self._PrintTestEnvironment(root=self.root.folder1)


    def _PrintTestEnvironment(self,root):
        """ print recursive all objects """

        print '....'*len(root.getPhysicalPath()),root.getId()

        folderObjs = []

        for id,obj in root.objectItems():

            if obj.meta_type in ['Folder','TestFolder']:
                folderObjs.append(obj)

            else:                
                print '    '*(1+len(root.getPhysicalPath())),obj.getId()

        for folder in folderObjs:
            self._PrintTestEnvironment(folder)



    def testPublicFunc(self):
        """ testing PublicFunc"""

        path = "/folder1/object1/public_func" 

        for user in USERS:
            res = self._request(path,u=user.auth())
            assert res.code==200, res(expected=200)


    def testPublicFuncWithWrongAuth(self):
        """ testing PublicFunc with wrong auth"""

        path = "/folder1/object1/public_func" 

        for user in USERS:
            res = self._request(path,u=user.auth()+'xx')
            assert res.code==200, res(expected=200)


    def testPrivateFunc(self):
        """ testing PrivateFunc"""

        path = "/folder1/object1/private_func" 

        for user in USERS:
            res = self._request(path,u=user.auth())
            assert res.code==401, res(expected=401)


    def testProtectedFunc(self):
        """ testing ProtectedFunc"""

        path = "/folder1/object1/protected_func" 

        for user in USERS:
            res = self._request(path,u=user.auth())

            if 'Manager' in user.roles:
                assert res.code==200, res(expected=200)
            else:
                assert res.code==401, res(expected=401)


    def _testDTMLPublicFunc(self):
        """ test DTML functions """

        path = "/folder1/object1/dtmlPublic" 

        for user in USERS:
            res = self._request(path,u=user.auth())
            assert res.code==200, res(expected=200)


    def testDTMLPrivateFunc(self):
        """ test DTML functions """

        path = "/folder1/object1/dtmlPrivate" 

        for user in USERS:
            res = self._request(path,u=user.auth())
            assert res.code==401, res(expected=401)


    def _testDTMLProtectedFunc(self):
        """ test DTML functions """

        path = "/folder1/object1/dtmlProtected" 

        for user in USERS:
            res = self._request(path,u=user.auth())

            if 'Manager' in user.roles:
                assert res.code==200, res(expected=200)
            else:
                assert res.code==401, res(expected=401)



    _reg = re.compile("Status: ([0-9]{1,4}) (.*)",re.I)

    def _request(self,*args,**kw):
        io =cStringIO.StringIO()
        kw['s']=io
        ZPublisher.Zope(*args,**kw)
        outp = io.getvalue()
        mo = self._reg.search(outp)

        code,txt = mo.groups()

        res = ResultObject()
        res.request     = args
        res.user        = kw.get('u','')
        res.code        = int(code)
        res.return_text = txt
        res.output      = outp

        return res

        
framework()

