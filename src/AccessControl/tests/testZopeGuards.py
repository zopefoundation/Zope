##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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
"""Test Zope Guards

Well, at least begin testing some of the functionality

$Id$
"""
import doctest
import unittest

import os
import operator
import sys

import ZODB


if sys.version_info >= (2, 5):
    from AccessControl.ZopeGuards import guarded_any, guarded_all
    MIN_MAX_TAKE_KEY = True
else:
    MIN_MAX_TAKE_KEY = False

try:
    __file__
except NameError:
    __file__ = os.path.abspath(sys.argv[1])
_FILEPATH = os.path.abspath( __file__ )
_HERE = os.path.dirname( _FILEPATH )

class SecurityManager:

    def __init__(self, reject=0):
        self.calls = []
        self.reject = reject

    def validate(self, *args):
        from AccessControl import Unauthorized
        self.calls.append(('validate', args))
        if self.reject:
            raise Unauthorized
        return 1

    def validateValue(self, *args):
        from AccessControl import Unauthorized
        self.calls.append(('validateValue', args))
        if self.reject:
            raise Unauthorized
        return 1

    def checkPermission(self, *args):
        self.calls.append(('checkPermission', args))
        return not self.reject

class GuardTestCase(unittest.TestCase):

    def setSecurityManager(self, manager):
        from AccessControl.SecurityManagement import get_ident
        from AccessControl.SecurityManagement import _managers
        key = get_ident()
        old = _managers.get(key)
        if manager is None:
            del _managers[key]
        else:
            _managers[key] = manager
        return old


class Method:

    def __init__(self, *args):
        self.args = args


class TestGuardedGetattr(GuardTestCase):

    def setUp(self):
        self.__sm = SecurityManager()
        self.__old = self.setSecurityManager(self.__sm)

    def tearDown(self):
        self.setSecurityManager(self.__old)

    def test_unauthorized(self):
        from AccessControl import Unauthorized
        from AccessControl.ZopeGuards import guarded_getattr
        obj, name = Method(), 'args'
        value = getattr(obj, name)
        rc = sys.getrefcount(value)
        self.__sm.reject = True
        self.assertRaises(Unauthorized, guarded_getattr, obj, name)
        self.assert_(self.__sm.calls)
        del self.__sm.calls[:]
        self.assertEqual(rc, sys.getrefcount(value))

    def test_calls_validate_for_unknown_type(self):
        from AccessControl.ZopeGuards import guarded_getattr
        guarded_getattr(self, 'test_calls_validate_for_unknown_type')
        self.assert_(self.__sm.calls)

    def test_attr_handler_table(self):
        from AccessControl import Unauthorized
        from AccessControl.ZopeGuards import guarded_getattr
        from AccessControl.SimpleObjectPolicies import ContainerAssertions
        d = {}
        _dict = type(d)
        old = ContainerAssertions.get(_dict)

        mytable = {'keys': 1,
                   'values': Method,
                   }
        ContainerAssertions[_dict] = mytable
        try:
            guarded_getattr(d, 'keys')
            self.assertEqual(len(self.__sm.calls), 0)
            values = guarded_getattr(d, 'values')
            self.assertEqual(values.__class__, Method)
            self.assertEqual(values.args, (d, 'values'))
            self.assertRaises(Unauthorized, guarded_getattr, d, 'items')
        finally:
            ContainerAssertions[_dict] = old


class TestDictGuards(GuardTestCase):

    def test_get_simple(self):
        from AccessControl.ZopeGuards import get_dict_get
        get = get_dict_get({'foo': 'bar'}, 'get')
        self.assertEqual(get('foo'), 'bar')

    def test_get_default(self):
        from AccessControl.ZopeGuards import get_dict_get
        get = get_dict_get({'foo': 'bar'}, 'get')
        self.failUnless(get('baz') is None)
        self.assertEqual(get('baz', 'splat'), 'splat')

    def test_get_validates(self):
        from AccessControl.ZopeGuards import get_dict_get
        sm = SecurityManager()
        old = self.setSecurityManager(sm)
        get = get_dict_get({'foo':GuardTestCase}, 'get')
        try:
            get('foo')
        finally:
            self.setSecurityManager(old)
        self.assert_(sm.calls)

    def test_pop_simple(self):
        from AccessControl.ZopeGuards import get_dict_pop
        pop = get_dict_pop({'foo': 'bar'}, 'pop')
        self.assertEqual(pop('foo'), 'bar')

    def test_pop_raises(self):
        from AccessControl.ZopeGuards import get_dict_pop
        pop = get_dict_pop({'foo': 'bar'}, 'pop')
        self.assertRaises(KeyError, pop, 'baz')

    def test_pop_default(self):
        from AccessControl.ZopeGuards import get_dict_pop
        pop = get_dict_pop({'foo': 'bar'}, 'pop')
        self.assertEqual(pop('baz', 'splat'), 'splat')

    def test_pop_validates(self):
        from AccessControl.ZopeGuards import get_dict_get
        sm = SecurityManager()
        old = self.setSecurityManager(sm)
        pop = get_dict_get({'foo':GuardTestCase}, 'pop')
        try:
            pop('foo')
        finally:
            self.setSecurityManager(old)
        self.assert_(sm.calls)

    if sys.version_info >= (2, 2):

        def test_iterkeys_simple(self):
            from AccessControl.ZopeGuards import get_iter
            d = {'foo':1, 'bar':2, 'baz':3}
            iterkeys = get_iter(d, 'iterkeys')
            keys = d.keys()
            keys.sort()
            ikeys = list(iterkeys())
            ikeys.sort()
            self.assertEqual(keys, ikeys)

        def test_iterkeys_empty(self):
            from AccessControl.ZopeGuards import get_iter
            iterkeys = get_iter({}, 'iterkeys')
            self.assertEqual(list(iterkeys()), [])

        def test_iterkeys_validates(self):
            from AccessControl.ZopeGuards import get_iter
            sm = SecurityManager()
            old = self.setSecurityManager(sm)
            iterkeys = get_iter({GuardTestCase: 1}, 'iterkeys')
            try:
                iterkeys().next()
            finally:
                self.setSecurityManager(old)
            self.assert_(sm.calls)

        def test_itervalues_simple(self):
            from AccessControl.ZopeGuards import get_iter
            d = {'foo':1, 'bar':2, 'baz':3}
            itervalues = get_iter(d, 'itervalues')
            values = d.values()
            values.sort()
            ivalues = list(itervalues())
            ivalues.sort()
            self.assertEqual(values, ivalues)

        def test_itervalues_empty(self):
            from AccessControl.ZopeGuards import get_iter
            itervalues = get_iter({}, 'itervalues')
            self.assertEqual(list(itervalues()), [])

        def test_itervalues_validates(self):
            from AccessControl.ZopeGuards import get_iter
            sm = SecurityManager()
            old = self.setSecurityManager(sm)
            itervalues = get_iter({GuardTestCase: 1}, 'itervalues')
            try:
                itervalues().next()
            finally:
                self.setSecurityManager(old)
            self.assert_(sm.calls)

class TestListGuards(GuardTestCase):

    def test_pop_simple(self):
        from AccessControl.ZopeGuards import get_list_pop
        pop = get_list_pop(['foo', 'bar', 'baz'], 'pop')
        self.assertEqual(pop(), 'baz')
        self.assertEqual(pop(0), 'foo')

    def test_pop_raises(self):
        from AccessControl.ZopeGuards import get_list_pop
        pop = get_list_pop([], 'pop')
        self.assertRaises(IndexError, pop)

    def test_pop_validates(self):
        from AccessControl.ZopeGuards import get_list_pop
        sm = SecurityManager()
        old = self.setSecurityManager(sm)
        pop = get_list_pop([GuardTestCase], 'pop')
        try:
            pop()
        finally:
            self.setSecurityManager(old)
        self.assert_(sm.calls)


class TestBuiltinFunctionGuards(GuardTestCase):

    def test_zip_fails(self):
        from AccessControl import Unauthorized
        from AccessControl.ZopeGuards import guarded_zip
        sm = SecurityManager(1) # rejects
        old = self.setSecurityManager(sm)
        self.assertRaises(Unauthorized, guarded_zip, [1,2,3], [3,2,1])
        self.assertRaises(Unauthorized, guarded_zip, [1,2,3], [1])
        self.setSecurityManager(old)

    def test_map_fails(self):
        from AccessControl import Unauthorized
        from AccessControl.ZopeGuards import guarded_map
        sm = SecurityManager(1) # rejects
        old = self.setSecurityManager(sm)
        self.assertRaises(Unauthorized, guarded_map, str, 
                          [1,2,3])
        self.assertRaises(Unauthorized, guarded_map, lambda x,y: x+y, 
                          [1,2,3], [3,2,1])
        self.setSecurityManager(old)

    if sys.version_info >= (2, 5):
        def test_all_fails(self):
            from AccessControl import Unauthorized
            sm = SecurityManager(1) # rejects
            old = self.setSecurityManager(sm)
            self.assertRaises(Unauthorized, guarded_all, [True,True,False])
            self.setSecurityManager(old)

        def test_any_fails(self):
            from AccessControl import Unauthorized
            sm = SecurityManager(1) # rejects
            old = self.setSecurityManager(sm)
            self.assertRaises(Unauthorized, guarded_any, [True,True,False])
            self.setSecurityManager(old)

    def test_min_fails(self):
        from AccessControl import Unauthorized
        from AccessControl.ZopeGuards import guarded_min
        sm = SecurityManager(1) # rejects
        old = self.setSecurityManager(sm)
        self.assertRaises(Unauthorized, guarded_min, [1,2,3])
        self.assertRaises(Unauthorized, guarded_min, 1,2,3)
        if MIN_MAX_TAKE_KEY:
            class MyDict(dict):  # guard() skips 'dict' values
                pass
            self.assertRaises(Unauthorized, guarded_min,
                              MyDict(x=1), MyDict(x=2),
                              key=operator.itemgetter('x'))
        self.setSecurityManager(old)

    def test_max_fails(self):
        from AccessControl import Unauthorized
        from AccessControl.ZopeGuards import guarded_max
        sm = SecurityManager(1) # rejects
        old = self.setSecurityManager(sm)
        self.assertRaises(Unauthorized, guarded_max, [1,2,3])
        self.assertRaises(Unauthorized, guarded_max, 1,2,3)
        if MIN_MAX_TAKE_KEY:
            class MyDict(dict):  # guard() skips 'dict' values
                pass
            self.assertRaises(Unauthorized, guarded_max, 
                              MyDict(x=1), MyDict(x=2),
                              key=operator.itemgetter('x'))
        self.setSecurityManager(old)

    def test_enumerate_fails(self):
        from AccessControl import Unauthorized
        from AccessControl.ZopeGuards import guarded_enumerate
        sm = SecurityManager(1) # rejects
        old = self.setSecurityManager(sm)
        enum = guarded_enumerate([1,2,3])
        self.assertRaises(Unauthorized, enum.next)
        self.setSecurityManager(old)

    def test_sum_fails(self):
        from AccessControl import Unauthorized
        from AccessControl.ZopeGuards import guarded_sum
        sm = SecurityManager(1) # rejects
        old = self.setSecurityManager(sm)
        self.assertRaises(Unauthorized, guarded_sum, [1,2,3])
        self.setSecurityManager(old)

    def test_zip_succeeds(self):
        from AccessControl.ZopeGuards import guarded_zip
        sm = SecurityManager() # accepts
        old = self.setSecurityManager(sm)
        self.assertEqual(guarded_zip([1,2,3], [3,2,1]), [(1,3),(2,2),(3,1)])
        self.assertEqual(guarded_zip([1,2,3], [1]), [(1,1)])
        self.setSecurityManager(old)

    def test_map_succeeds(self):
        from AccessControl.ZopeGuards import guarded_map
        sm = SecurityManager() # accepts
        old = self.setSecurityManager(sm)
        self.assertEqual(guarded_map(str, [1,2,3]), ['1','2','3'])
        self.assertEqual(guarded_map(lambda x,y: x+y, [1,2,3], [3,2,1]), 
                         [4,4,4])
        self.setSecurityManager(old)

    if sys.version_info >= (2, 5):
        def test_all_succeeds(self):
            sm = SecurityManager() # accepts
            old = self.setSecurityManager(sm)
            self.assertEqual(guarded_all([True,True,False]), False)
            self.setSecurityManager(old)

        def test_any_succeeds(self):
            sm = SecurityManager() # accepts
            old = self.setSecurityManager(sm)
            self.assertEquals(guarded_any([True,True,False]), True)
            self.setSecurityManager(old)

    def test_min_succeeds(self):
        from AccessControl.ZopeGuards import guarded_min
        sm = SecurityManager() # accepts
        old = self.setSecurityManager(sm)
        self.assertEqual(guarded_min([1,2,3]), 1)
        self.assertEqual(guarded_min(1,2,3), 1)
        if MIN_MAX_TAKE_KEY:
            class MyDict(dict):  # guard() skips 'dict' values
                pass
            self.assertEqual(guarded_min(MyDict(x=1), MyDict(x=2),
                                         key=operator.itemgetter('x')),
                             {'x':1})
        self.setSecurityManager(old)

    def test_max_succeeds(self):
        from AccessControl.ZopeGuards import guarded_max
        sm = SecurityManager() # accepts
        old = self.setSecurityManager(sm)
        self.assertEqual(guarded_max([1,2,3]), 3)
        self.assertEqual(guarded_max(1,2,3), 3)
        if MIN_MAX_TAKE_KEY:
            class MyDict(dict):  # guard() skips 'dict' values
                pass
            self.assertEqual(guarded_max(MyDict(x=1), MyDict(x=2),
                                         key=operator.itemgetter('x')),
                             {'x':2})
        self.setSecurityManager(old)

    def test_enumerate_succeeds(self):
        from AccessControl.ZopeGuards import guarded_enumerate
        sm = SecurityManager() # accepts
        old = self.setSecurityManager(sm)
        enum = guarded_enumerate([1,2,3])
        self.assertEqual(enum.next(), (0,1))
        self.assertEqual(enum.next(), (1,2))
        self.assertEqual(enum.next(), (2,3))
        self.assertRaises(StopIteration, enum.next)
        self.setSecurityManager(old)

    def test_sum_succeeds(self):
        from AccessControl.ZopeGuards import guarded_sum
        sm = SecurityManager() # accepts
        old = self.setSecurityManager(sm)
        self.assertEqual(guarded_sum([1,2,3]), 6)
        self.assertEqual(guarded_sum([1,2,3], start=36), 42)
        self.setSecurityManager(old)

    def test_apply(self):
        from AccessControl import Unauthorized
        from AccessControl.ZopeGuards import safe_builtins
        sm = SecurityManager(1) # rejects
        old = self.setSecurityManager(sm)
        gapply = safe_builtins['apply']
        def f(a=1, b=2):
            return a+b
        # This one actually succeeds, because apply isn't given anything
        # to unpack.
        self.assertEqual(gapply(f), 3)
        # Likewise, because the things passed are empty.
        self.assertEqual(gapply(f, (), {}), 3)

        self.assertRaises(Unauthorized, gapply, f, [1])
        self.assertRaises(Unauthorized, gapply, f, (), {'a': 2})
        self.assertRaises(Unauthorized, gapply, f, [1], {'a': 2})

        sm = SecurityManager(0) # accepts
        self.setSecurityManager(sm)
        self.assertEqual(gapply(f), 3)
        self.assertEqual(gapply(f, (), {}), 3)
        self.assertEqual(gapply(f, [0]), 2)
        self.assertEqual(gapply(f, [], {'b': 18}), 19)
        self.assertEqual(gapply(f, [10], {'b': 1}), 11)

        self.setSecurityManager(old)

class TestGuardedDictListTypes(unittest.TestCase):

    def testDictCreation(self):
        from AccessControl.ZopeGuards import safe_builtins
        d = safe_builtins['dict']
        self.assertEquals(d(), {})
        self.assertEquals(d({1:2}), {1:2})
        self.assertEquals(d(((1,2),)), {1:2})
        self.assertEquals(d(foo=1), {"foo":1})
        self.assertEquals(d.fromkeys((1,2,3)), {1:None, 2:None, 3:None})
        self.assertEquals(d.fromkeys((1,2,3), 'f'), {1:'f', 2:'f', 3:'f'})

    def testListCreation(self):
        from AccessControl.ZopeGuards import safe_builtins
        l = safe_builtins['list']
        self.assertEquals(l(), [])
        self.assertEquals(l([1,2,3]), [1,2,3])
        x = [3,2,1]
        self.assertEquals(l(x), [3,2,1])
        if sys.version_info >= (2, 4):
            self.assertEquals(sorted(x), [1,2,3])

class TestRestrictedPythonApply(GuardTestCase):

    def test_apply(self):
        from AccessControl import Unauthorized
        from AccessControl.ZopeGuards import guarded_apply
        sm = SecurityManager(1) # rejects
        old = self.setSecurityManager(sm)
        gapply = guarded_apply
        def f(a=1, b=2):
            return a+b
        # This one actually succeeds, because apply isn't given anything
        # to unpack.
        self.assertEqual(gapply(*(f,)), 3)
        # Likewise, because the things passed are empty.
        self.assertEqual(gapply(*(f,), **{}), 3)

        self.assertRaises(Unauthorized, gapply, *(f, 1))
        self.assertRaises(Unauthorized, gapply, *(f,), **{'a': 2})
        self.assertRaises(Unauthorized, gapply, *(f, 1), **{'a': 2})

        sm = SecurityManager(0) # accepts
        self.setSecurityManager(sm)
        self.assertEqual(gapply(*(f,)), 3)
        self.assertEqual(gapply(*(f,), **{}), 3)
        self.assertEqual(gapply(*(f, 0)), 2)
        self.assertEqual(gapply(*(f,), **{'b': 18}), 19)
        self.assertEqual(gapply(*(f, 10), **{'b': 1}), 11)

        self.setSecurityManager(old)


# Map function name to the # of times it's been called.
wrapper_count = {}
class FuncWrapper:
    def __init__(self, funcname, func):
        self.funcname = funcname
        wrapper_count[funcname] = 0
        self.func = func

    def __call__(self, *args, **kws):
        wrapper_count[self.funcname] += 1
        return self.func(*args, **kws)

    def __repr__(self):
        return "<FuncWrapper around %r>" % self.func

# Given the high wall between AccessControl and RestrictedPython, I suppose
# the next one could be called an integration test.  But we're simply
# trying to run restricted Python with the *intended* implementations of
# the special wrappers here, so no apologies.
_ProtectedBase = None

class TestActualPython(GuardTestCase):

    _old_mgr = _old_policy = _marker = []

    def setUp(self):
        self._wrapped_dicts = []

    def tearDown( self ):
        self._restorePolicyAndManager()
        for munged, orig in self._wrapped_dicts:
            munged.update(orig)
        del self._wrapped_dicts

    def _initPolicyAndManager(self, manager=None):
        from AccessControl.SecurityManagement import get_ident
        from AccessControl.SecurityManagement import _managers
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.SecurityManager import setSecurityPolicy
        from AccessControl.ZopeSecurityPolicy import ZopeSecurityPolicy

        class UnderprivilegedUser:
            """ Anonymous USer for unit testing purposes.
            """
            def getId(self):
                return 'Underprivileged User'

            getUserName = getId

            def allowed(self, object, object_roles=None):
                return 0

            def getRoles(self):
                return ()

        self._policy = ZopeSecurityPolicy()
        self._old_policy = setSecurityPolicy(self._policy)

        if manager is None:
            thread_id = get_ident()
            self._old_mgr = manager=_managers.get(thread_id, self._marker)
            newSecurityManager(None, UnderprivilegedUser())
        else:
            self._old_mgr = self.setSecurityManager(manager)

    def _restorePolicyAndManager(self):
        from AccessControl.SecurityManagement import noSecurityManager
        from AccessControl.SecurityManager import setSecurityPolicy

        if self._old_mgr is not self._marker:
            self.setSecurityManager(self._old_mgr)
        else:
            noSecurityManager()

        if self._old_policy is not self._marker:
            setSecurityPolicy(self._old_policy)

    def _getProtectedBaseClass(self):

        from AccessControl.SecurityInfo import ClassSecurityInfo
        from ExtensionClass import Base
        from App.class_init import InitializeClass

        global _ProtectedBase
        if _ProtectedBase is None:

            class ProtectedBase(Base):
                security = ClassSecurityInfo()

                security.declarePrivate('private_method')
                def private_method(self):
                    return 'private_method called'

            InitializeClass(ProtectedBase)
            _ProtectedBase = ProtectedBase

        return _ProtectedBase

    def testPython(self):
        from RestrictedPython.tests import verify

        code, its_globals = self._compile("actual_python.py")
        verify.verify(code)

        # Fiddle the global and safe-builtins dicts to count how many times
        # the special functions are called.
        self._wrap_replaced_dict_callables(its_globals)
        self._wrap_replaced_dict_callables(its_globals['__builtins__'])

        sm = SecurityManager()
        old = self.setSecurityManager(sm)
        try:
            exec code in its_globals
        finally:
            self.setSecurityManager(old)

        # Use wrapper_count to determine coverage.
        ## print wrapper_count # uncomment to see wrapper names & counts
        untouched = [k for k, v in wrapper_count.items() if v == 0]
        if untouched:
            untouched.sort()
            self.fail("Unexercised wrappers: %r" % untouched)

    def testPythonRealAC(self):
        code, its_globals = self._compile("actual_python.py")
        exec code in its_globals

    def test_derived_class_normal(self):
        from AccessControl import Unauthorized
        from RestrictedPython.tests import verify

        NORMAL_SCRIPT = """
class Normal(ProtectedBase):
    pass

normal = Normal()
print normal.private_method()
"""
        code, its_globals = self._compile_str(NORMAL_SCRIPT, 'normal_script')
        its_globals['ProtectedBase'] = self._getProtectedBaseClass()
        verify.verify(code)

        self._initPolicyAndManager()

        try:
            exec code in its_globals
        except Unauthorized:
            pass
        else:
            self.fail("Didn't raise Unauthorized: \n%s" % 
                        its_globals['_print']())

    def test_derived_class_sneaky_en_suite(self):

        #  Disallow declaration of security-affecting names in classes
        #  defined in restricted code (compile-time check).
        from RestrictedPython.tests import verify

        SNEAKY_SCRIPT = """
class Sneaky(ProtectedBase):
    private_method__roles__ = None


sneaky = Sneaky()
print sneaky.private_method()
"""
        try:
            code, its_globals = self._compile_str(SNEAKY_SCRIPT,
                                                  'sneaky_script')
        except SyntaxError:
            pass
        else:
            self.fail("Didn't raise SyntaxError!")

    def test_derived_sneaky_post_facto(self):

        #  Assignment to a class outside its suite fails at
        #  compile time with a SyntaxError.
        from RestrictedPython.tests import verify

        SNEAKY_SCRIPT = """
class Sneaky(ProtectedBase):
    pass

Sneaky.private_method__roles__ = None

sneaky = Sneaky()
print sneaky.private_method()
"""
        try:
            code, its_globals = self._compile_str(SNEAKY_SCRIPT, 'sneaky_script')
        except SyntaxError:
            pass
        else:
            self.fail("Didn't raise SyntaxError!")

    def test_derived_sneaky_instance(self):

        #  Assignment of security-sensitive names to an instance
        #  fails at compile time with a SyntaxError.
        from RestrictedPython.tests import verify

        SNEAKY_SCRIPT = """
class Sneaky(ProtectedBase):
    pass

sneaky = Sneaky()
sneaky.private_method__roles__ = None
print sneaky.private_method()
"""
        try:
            code, its_globals = self._compile_str(SNEAKY_SCRIPT,
                                                  'sneaky_script')
        except SyntaxError:
            pass
        else:
            self.fail("Didn't raise SyntaxError!")


    def test_dict_access(self):
        from RestrictedPython.tests import verify

        SIMPLE_DICT_ACCESS_SCRIPT = """
def foo(text):
    return text

kw = {'text':'baz'}
print foo(**kw)

kw = {'text':True}
print foo(**kw)
"""
        code, its_globals = self._compile_str(SIMPLE_DICT_ACCESS_SCRIPT, 'x')
        verify.verify(code)

        sm = SecurityManager()
        old = self.setSecurityManager(sm)
        try:
            exec code in its_globals
        finally:
            self.setSecurityManager(old)

        self.assertEqual(its_globals['_print'](),
                        'baz\nTrue\n')
        
    def _compile_str(self, text, name):
        from RestrictedPython import compile_restricted
        from AccessControl.ZopeGuards import get_safe_globals, guarded_getattr

        code = compile_restricted(text, name, 'exec')

        g = get_safe_globals()
        g['_getattr_'] = guarded_getattr
        g['__debug__'] = 1  # so assert statements are active
        g['__name__'] = __name__ # so classes can be defined in the script
        return code, g

    # Compile code in fname, as restricted Python. Return the
    # compiled code, and a safe globals dict for running it in.
    # fname is the string name of a Python file; it must be found
    # in the same directory as this file.
    def _compile(self, fname):
        from RestrictedPython import compile_restricted
        from AccessControl.ZopeGuards import get_safe_globals, guarded_getattr

        fn = os.path.join( _HERE, fname)
        text = open(fn).read()
        return self._compile_str(text, fn)

    # d is a dict, the globals for execution or our safe builtins.
    # The callable values which aren't the same as the corresponding
    # entries in __builtin__ are wrapped in a FuncWrapper, so we can
    # tell whether they're executed.
    def _wrap_replaced_dict_callables(self, d):
        import __builtin__
        orig = d.copy()
        self._wrapped_dicts.append((d, orig))
        for k, v in d.items():
            if callable(v) and v is not getattr(__builtin__, k, None):
                d[k] = FuncWrapper(k, v)

def test_inplacevar():
    """
Verify the correct behavior of protected_inplacevar.

    >>> from AccessControl.ZopeGuards import protected_inplacevar

Basic operations on objects without inplace slots work as expected:

    >>> protected_inplacevar('+=', 1, 2)
    3
    >>> protected_inplacevar('-=', 5, 2)
    3
    >>> protected_inplacevar('*=', 5, 2)
    10
    >>> protected_inplacevar('/=', 6, 2)
    3
    >>> protected_inplacevar('%=', 5, 2)
    1
    >>> protected_inplacevar('**=', 5, 2)
    25
    >>> protected_inplacevar('<<=', 5, 2)
    20
    >>> protected_inplacevar('>>=', 5, 2)
    1
    >>> protected_inplacevar('&=', 5, 2)
    0
    >>> protected_inplacevar('^=', 7, 2)
    5
    >>> protected_inplacevar('|=', 5, 2)
    7

Inplace operations are allowed on lists:

    >>> protected_inplacevar('+=', [1], [2])
    [1, 2]

    >>> protected_inplacevar('*=', [1], 2)
    [1, 1]

But not on custom objects:

    >>> class C:
    ...     def __iadd__(self, other):
    ...         return 42
    >>> protected_inplacevar('+=', C(), 2)    # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    ...
    TypeError: Augmented assignment to C objects is not allowed in
    untrusted code
"""

if sys.version_info[:2] >= (2, 4):
    def test_inplacevar_for_py24():
        """
protected_inplacevar allows inplce ops on sets:

    >>> from AccessControl.ZopeGuards import protected_inplacevar
    >>> s = set((1,2,3,4))
    >>> sorted(protected_inplacevar('-=', s, set((1, 3))))
    [2, 4]
    >>> sorted(s)
    [2, 4]
    
    >>> sorted(protected_inplacevar('|=', s, set((1, 3, 9))))
    [1, 2, 3, 4, 9]
    >>> sorted(s)
    [1, 2, 3, 4, 9]

    >>> sorted(protected_inplacevar('&=', s, set((1, 2, 3, 9))))
    [1, 2, 3, 9]
    >>> sorted(s)
    [1, 2, 3, 9]

    >>> sorted(protected_inplacevar('^=', s, set((1, 3, 7, 8))))
    [2, 7, 8, 9]
    >>> sorted(s)
    [2, 7, 8, 9]

"""

def test_suite():
    suite = unittest.TestSuite([
        doctest.DocTestSuite(),
        ])
    for cls in (TestGuardedGetattr,
                TestDictGuards,
                TestBuiltinFunctionGuards,
                TestListGuards,
                TestGuardedDictListTypes,
                TestRestrictedPythonApply,
                TestActualPython,
                ):
        suite.addTest(unittest.makeSuite(cls))
    return suite


if __name__ == '__main__':
    unittest.main()
