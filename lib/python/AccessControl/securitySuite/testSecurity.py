#!/usr/bin/env python2.1

##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

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


# let's define some permissions first

MAGIC_PERMISSION1 = 'Magic Permission 1'
MAGIC_PERMISSION2 = 'Magic Permission 2'


##############################################################################
# ResultObject class
##############################################################################

class ResultObject:
    """ result object used for keeping results from the 
        ZPublisher.Zope() calls 
    """

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

Globals.InitializeClass(TestObject)


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

Globals.InitializeClass(TestFolder)


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


##############################################################################
# Security tests
##############################################################################

class SecurityBase(unittest.TestCase) :

    status_regex = re.compile("Status: ([0-9]{1,4}) (.*)",re.I)\

    ################################################################
    # set up the test hierachy of objects
    ################################################################

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
        
        get_transaction().commit()


    ################################################################
    # print the object hierachy
    ################################################################

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


    ################################################################
    # Check functions for permissions, roles and friends
    ################################################################

    def _checkPermission(self, user, hier, perm, expected):
        """ low level permission check """

        s = "self.root.test.%s" % hier
        obj = eval(s)

        res = user.has_permission(perm,obj)

        if res != expected:        
            raise AssertionError, \
                self._perm_debug (s,perm,res,expected)


    def _checkRoles(self,hier,expected_roles=()):
        """ check roles for an object """
        
        s = "self.root.test.%s.__roles__" % hier
        roles = eval(s)

        if roles==None or len(roles)==0: 
            roles=(None,)
    
        for r in roles:
            if not r in expected_roles:
                raise AssertionError, self._roles_debug(hier,roles,expected_roles)
            

    ################################################################
    # Debugging helpers when raising AssertionError
    ################################################################

    def _perm_debug(self, obj , perm, res, expected):
        s = '' 
        s+=' Object: %s' % obj
        s+=', Permission: %s' % perm 
        s+=', has permission: %s' % res 
        s+=', expected: %s' % expected

        return s
        

    def _roles_debug(self,hier,expected_roles,got_roles):

        s = ''
        s+='Object: %s' % hier
        s+=", has roles: %s " % got_roles        
        s+=", expected roles: %s" % expected_roles

        return s
 
    def _request(self,*args,**kw):
        """ perform a Zope request """

        io =cStringIO.StringIO()
        kw['fp']=io
        ZPublisher.Zope(*args,**kw)
        outp = io.getvalue()
        mo = self.status_regex.search(outp)

        code,txt = mo.groups()

        res = ResultObject()
        res.request     = args
        res.user        = kw.get('u','')
        res.code        = int(code)
        res.return_text = txt
        res.output      = outp

        return res


class SecurityTests(SecurityBase):


    def testAttributeAccess(self):
        """ check access to attributes """

        obj = self.root.test.f2.f3.obj3

        try:    
            x = obj.public_attr
            obj.public_attr = 'blabla'
        except: raise AssertionError,'this should work !'    

        try:    
            x = obj._protected_attr
            raise AssertionError,'this should not work !'    
        except AssertionError: 
                raise
            
        try:    
            obj._protected_attr = "blalbla"
            raise AssertionError,'this should not work !'    
        except AssertionError: 
                raise


    def testNobody(self):
        """ check permissions for nobody user """

        self._checkPermission(nobody,'f1',   'View',1) 
        self._checkPermission(nobody,'f2',   'View',1) 
        self._checkPermission(nobody,'f2.f3','View',1) 
        self._checkPermission(nobody,'f1',   MAGIC_PERMISSION1, None) 
        self._checkPermission(nobody,'f2',   MAGIC_PERMISSION1, None) 
        self._checkPermission(nobody,'f2.f3',MAGIC_PERMISSION1, None) 


    def testPermissionAccess(self):
        """ check permission based access """

        self._checkRoles('f2.f3.obj3.public_func',     (None,))    
        self._checkRoles('f2.f3.obj3.protected_func',  ('Manager','Owner'))    
        self._checkRoles('f2.f3.obj3.manage_func',     ('Manager',))    
        self._checkRoles('f2.f3.obj3.private_func',    ('Manager',))    


    def testZPublisherAccess(self):
        """ test access through ZPublisher """

        _r = [ ('/test/f1/',None,200),
               ('/test/f1/anonobj','manager:123',200),
              ]

        for path,auth,expected in _r:
            if auth:
                res = self._request(path,u=auth)
            else:
                res = self._request(path)

            assert res.code==expected, (path,auth,expected,res)

        
framework()
