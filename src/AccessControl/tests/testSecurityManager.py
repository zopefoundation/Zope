##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
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
"""Tests for the SecurityManager implementations
"""

import unittest

_THREAD_ID = 123

class DummyContext:

    def __init__(self):
        self.user = object()
        self.stack = []

class DummyPolicy:

    CHECK_PERMISSION_ARGS = None
    CHECK_PERMISSION_RESULT = object()

    VALIDATE_ARGS = None

    def checkPermission(self, *args):
        self.CHECK_PERMISSION_ARGS = args
        return self.CHECK_PERMISSION_RESULT

    def validate(self, *args):
        self.VALIDATE_ARGS = args
        return True

class ExecutableObject:
    def __init__(self, new_policy):
        self._new_policy = new_policy

    def _customSecurityPolicy(self):
        return self._new_policy

class ISecurityManagerConformance:

    def test_conforms_to_ISecurityManager(self):
        from AccessControl.interfaces import ISecurityManager
        from zope.interface.verify import verifyClass
        verifyClass(ISecurityManager, self._getTargetClass())

class SecurityManagerTestBase(unittest.TestCase):

    def _makeOne(self, thread_id, context):
        return self._getTargetClass()(thread_id, context)

    def test_getUser(self):
        context = DummyContext()
        mgr = self._makeOne(_THREAD_ID, context)
        self.failUnless(mgr.getUser() is context.user)

    def test_calledByExecutable_no_stack(self):
        context = DummyContext()
        mgr = self._makeOne(_THREAD_ID, context)
        self.failIf(mgr.calledByExecutable())

    def test_calledByExecutable_with_stack(self):
        context = DummyContext()
        mgr = self._makeOne(_THREAD_ID, context)
        executableObject = object()
        mgr.addContext(executableObject)
        self.failUnless(mgr.calledByExecutable())

    def test_addContext_no_custom_policy(self):
        context = DummyContext()
        mgr = self._makeOne(_THREAD_ID, context)
        original_policy = mgr._policy
        executableObject = object()
        mgr.addContext(executableObject)
        self.failUnless(mgr._policy is original_policy)

    def test_addContext_with_custom_policy(self):
        context = DummyContext()
        mgr = self._makeOne(_THREAD_ID, context)
        new_policy = DummyPolicy()
        executableObject = ExecutableObject(new_policy)
        mgr.addContext(executableObject)
        self.failUnless(mgr._policy is new_policy)

    def test_addContext_with_custom_policy_then_none(self):
        context = DummyContext()
        mgr = self._makeOne(_THREAD_ID, context)
        original_policy = mgr._policy
        new_policy = DummyPolicy()
        executableObject = ExecutableObject(new_policy)
        mgr.addContext(executableObject)
        mgr.addContext(object())
        self.failUnless(mgr._policy is original_policy)

    def test_removeContext_pops_items_above_EO(self):
        context = DummyContext()
        ALPHA, BETA, GAMMA, DELTA = object(), object(), object(), object()
        context.stack.append(ALPHA)
        context.stack.append(BETA)
        context.stack.append(GAMMA)
        context.stack.append(DELTA)
        mgr = self._makeOne(_THREAD_ID, context)

        mgr.removeContext(GAMMA)

        self.assertEqual(len(context.stack), 2)
        self.failUnless(context.stack[0] is ALPHA)
        self.failUnless(context.stack[1] is BETA)

    def test_removeContext_last_EO_restores_default_policy(self):
        context = DummyContext()
        mgr = self._makeOne(_THREAD_ID, context)
        original_policy = mgr._policy
        new_policy = mgr._policy = DummyPolicy()
        top = object()
        context.stack.append(top)
        mgr.removeContext(top)
        self.failUnless(mgr._policy is original_policy)

    def test_removeContext_with_top_having_custom_policy(self):
        context = DummyContext()
        mgr = self._makeOne(_THREAD_ID, context)
        new_policy = DummyPolicy()
        context.stack.append(ExecutableObject(new_policy))
        top = object()
        context.stack.append(top)
        mgr.removeContext(top)
        self.failUnless(mgr._policy is new_policy)

    def test_removeContext_with_top_having_no_custom_policy(self):
        context = DummyContext()
        mgr = self._makeOne(_THREAD_ID, context)
        original_policy = mgr._policy
        new_policy = DummyPolicy()
        executableObject = ExecutableObject(new_policy)
        context.stack.append(executableObject)
        top = object()
        context.stack.append(top)
        mgr.removeContext(executableObject)
        self.failUnless(mgr._policy is original_policy)

    def test_checkPermission_delegates_to_policy(self):
        context = DummyContext()
        PERMISSION = 'PERMISSION'
        TARGET = object()
        mgr = self._makeOne(_THREAD_ID, context)
        new_policy = mgr._policy = DummyPolicy()
        result = mgr.checkPermission(PERMISSION, TARGET)
        self.failUnless(result is DummyPolicy.CHECK_PERMISSION_RESULT)
        self.failUnless(new_policy.CHECK_PERMISSION_ARGS[0] is PERMISSION)
        self.failUnless(new_policy.CHECK_PERMISSION_ARGS[1] is TARGET)
        self.failUnless(new_policy.CHECK_PERMISSION_ARGS[2] is context)

    def test_validate_without_roles_delegates_to_policy(self):
        from AccessControl.SimpleObjectPolicies import _noroles

        context = DummyContext()
        ACCESSED = object()
        CONTAINER = object()
        NAME = 'NAME'
        VALUE = object()
        mgr = self._makeOne(_THREAD_ID, context)
        new_policy = mgr._policy = DummyPolicy()

        result = mgr.validate(ACCESSED,
                              CONTAINER,
                              NAME,
                              VALUE,
                             )

        self.failUnless(result)
        self.assertEqual(len(new_policy.VALIDATE_ARGS), 5)
        self.failUnless(new_policy.VALIDATE_ARGS[0] is ACCESSED)
        self.failUnless(new_policy.VALIDATE_ARGS[1] is CONTAINER)
        self.assertEqual(new_policy.VALIDATE_ARGS[2], NAME)
        self.failUnless(new_policy.VALIDATE_ARGS[3] is VALUE)
        self.failUnless(new_policy.VALIDATE_ARGS[4] is context)

    def test_validate_with_roles_delegates_to_policy(self):
        from AccessControl.SimpleObjectPolicies import _noroles

        context = DummyContext()
        ACCESSED = object()
        CONTAINER = object()
        NAME = 'NAME'
        VALUE = object()
        ROLES = ('Hamlet', 'Othello')
        mgr = self._makeOne(_THREAD_ID, context)
        new_policy = mgr._policy = DummyPolicy()

        result = mgr.validate(ACCESSED,
                              CONTAINER,
                              NAME,
                              VALUE,
                              ROLES,
                             )

        self.failUnless(result)
        self.assertEqual(len(new_policy.VALIDATE_ARGS), 6)
        self.failUnless(new_policy.VALIDATE_ARGS[0] is ACCESSED)
        self.failUnless(new_policy.VALIDATE_ARGS[1] is CONTAINER)
        self.assertEqual(new_policy.VALIDATE_ARGS[2], NAME)
        self.failUnless(new_policy.VALIDATE_ARGS[3] is VALUE)
        self.failUnless(new_policy.VALIDATE_ARGS[4] is context)
        self.assertEqual(new_policy.VALIDATE_ARGS[5], ROLES)

    def test_DTMLValidate_delegates_to_policy_validate(self):
        from AccessControl.SimpleObjectPolicies import _noroles

        context = DummyContext()
        ACCESSED = object()
        CONTAINER = object()
        NAME = 'NAME'
        VALUE = object()
        MD = {}
        mgr = self._makeOne(_THREAD_ID, context)
        new_policy = mgr._policy = DummyPolicy()

        result = mgr.DTMLValidate(ACCESSED,
                                  CONTAINER,
                                  NAME,
                                  VALUE,
                                  MD,
                                 )

        self.failUnless(result)
        self.assertEqual(len(new_policy.VALIDATE_ARGS), 5)
        self.failUnless(new_policy.VALIDATE_ARGS[0] is ACCESSED)
        self.failUnless(new_policy.VALIDATE_ARGS[1] is CONTAINER)
        self.assertEqual(new_policy.VALIDATE_ARGS[2], NAME)
        self.failUnless(new_policy.VALIDATE_ARGS[3] is VALUE)
        self.failUnless(new_policy.VALIDATE_ARGS[4] is context)

class PythonSecurityManagerTests(SecurityManagerTestBase,
                                 ISecurityManagerConformance,
                                ):

    def _getTargetClass(self):
        from AccessControl.ImplPython import SecurityManager
        return SecurityManager


# N.B.:  The C version mixes in the Python version, which is why we
#        can test for conformance to ISecurityManager.
class C_SecurityManagerTests(SecurityManagerTestBase,
                             ISecurityManagerConformance,
                            ):

    def _getTargetClass(self):
        from AccessControl.ImplC import SecurityManager
        return SecurityManager


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( PythonSecurityManagerTests ) )
    suite.addTest( unittest.makeSuite( C_SecurityManagerTests ) )
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

