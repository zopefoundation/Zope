##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test Bindings

$Id: testBindings.py,v 1.2 2004/01/15 23:09:06 tseaver Exp $
"""

import unittest
import Zope
import AccessControl.SecurityManagement
from AccessControl import Unauthorized
from Testing.makerequest import makerequest
from Products.PythonScripts.PythonScript import PythonScript


class TransactionalTest( unittest.TestCase ):

    def setUp( self ):
        if hasattr(Zope, 'startup'):
            Zope.startup()
        get_transaction().begin()
        self.connection = Zope.DB.open()
        self.root =  self.connection.root()[ 'Application' ]

    def tearDown( self ):
        get_transaction().abort()
        self.connection.close()


class RequestTest( TransactionalTest ):

    def setUp(self):
        TransactionalTest.setUp(self)
        root = self.root = makerequest(self.root)
        self.REQUEST  = root.REQUEST
        self.RESPONSE = root.REQUEST.RESPONSE


class SecurityManager:

    def __init__(self, reject=0):
        self.calls = []
        self.reject = reject

    def validate(self, *args):
        self.calls.append(('validate', args))
        if self.reject:
            raise Unauthorized
        return 1

    def validateValue(self, *args):
        self.calls.append(('validateValue', args))
        if self.reject:
            raise Unauthorized
        return 1

    def checkPermission(self, *args):
        self.calls.append(('checkPermission', args))
        return not self.reject
        
    def addContext(self, *args):
        self.calls.append(('addContext', args))
        return 1
        
    def removeContext(self, *args):
        self.calls.append(('removeContext', args))
        return 1
        
class GuardTestCase(RequestTest):

    def setSecurityManager(self, manager):
        key = AccessControl.SecurityManagement.get_ident()
        old = AccessControl.SecurityManagement._managers.get(key)
        if manager is None:
            del AccessControl.SecurityManagement._managers[key]
        else:
            AccessControl.SecurityManagement._managers[key] = manager

        return old
        
        
class TestBindings(GuardTestCase):

    def setUp(self):
        RequestTest.setUp(self)
        self.sm = SecurityManager(reject=1)
        self.old = self.setSecurityManager(self.sm)

    def tearDown(self):
        self.setSecurityManager(self.old)
        TransactionalTest.tearDown(self)

    def _newPS(self, txt, bind=None):
        ps = PythonScript('ps')
        #ps.ZBindings_edit(bind or {})
        ps.write(txt)
        ps._makeFunction()
        return ps
    
    def test_fail_container(self):
        container_ps = self._newPS('return container')
        self.root._setOb('container_ps', container_ps)
        container_ps = self.root._getOb('container_ps')
        self.assertRaises(Unauthorized, container_ps)

    def test_fail_context(self):
        context_ps = self._newPS('return context')
        self.root._setOb('context_ps', context_ps)
        context_ps = self.root._getOb('context_ps')
        self.assertRaises(Unauthorized, context_ps)
    

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBindings))
    return suite


if __name__ == '__main__':
    unittest.main()
