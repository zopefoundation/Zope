from unittest import TestCase, TestSuite, makeSuite, main

import Testing
import Zope2
Zope2.startup()

from Acquisition import Implicit
from ZPublisher.BaseRequest import BaseRequest
from ZPublisher.HTTPResponse import HTTPResponse


# Various post traversal methods

pt_simple_was_run = 0

def pt_simple():
    global pt_simple_was_run 
    pt_simple_was_run = 1
    pass

def pt_static_arg(request, b):
    request.set('b', b)
    pass

def pt_simple_redirect(a):
    return a

def pt_chain_test(request, string):
    request.set('a', request.get('a', '') + string)

class DummyObjectBasic(Implicit):
    """ Dummy class with docstring.
    """

    def _setObject(self, id, object):
        setattr(self, id, object)
        return getattr(self, id)

    def view(self):
        """ Attribute with docstring.
        """
        return 'view content'

class DummyObjectWithPTHook(DummyObjectBasic):
    """ Dummy class with docstring.
    """

    traversal = []

    def __before_publishing_traverse__(self, object, REQUEST):
        for x in self.traversal:
            REQUEST.post_traverse(*x)

class TestBaseRequestPT(TestCase):

    def setUp(self):
        self.root = DummyObjectBasic()
        self.f1 = self.root._setObject('folder', DummyObjectBasic() )
        self.f1._setObject('objBasic', DummyObjectWithPTHook() )

    def makeBaseRequest(self):
        response = HTTPResponse()
        environment = { 'URL': '',
                        'PARENTS': [self.root],
                        'steps': [],
                        '_hacked_path': 0,
                        '_test_counter': 0,
                        'response': response }
        return BaseRequest(environment)

    def test_post_basic(self):
        global pt_simple_was_run
        pt_simple_was_run = 0
        r = self.makeBaseRequest()
        
        # Set hook
        self.f1.objBasic.traversal = [(pt_simple,)]
        x = r.traverse('folder/objBasic')
        
        # Object should be self.f1.objBasic
        self.assertEqual(x, self.f1.objBasic)
        self.assertEqual(pt_simple_was_run, 1)

        self.f1.objBasic.traversal = []

    def test_post_arg(self):

        r = self.makeBaseRequest()
        b = 1

        self.f1.objBasic.traversal = [(pt_static_arg, (r, b))]
        x = r.traverse('folder/objBasic')

        # Object should have been traversed normally
        self.assertEqual(x, self.f1.objBasic)
        self.assertEqual(r.get('b', 0), b)

        self.f1.objBasic.traversal = []

    def test_hook_chain(self):

        r = self.makeBaseRequest()

        self.f1.objBasic.traversal = [ (pt_chain_test, (r, 'a')),
                                       (pt_chain_test, (r, 'b')),
                                       (pt_chain_test, (r, 'c')),
                                       (pt_chain_test, (r, 'd'))]

        x = r.traverse('folder/objBasic')
        self.assertEqual(r.get('a',''), 'abcd')

        self.f1.objBasic.traversal = []

    def test_hook_redirect(self):
        r = self.makeBaseRequest()
        check = []
        self.f1.objBasic.traversal = [(pt_simple_redirect, (check,))]

        x = r.traverse('folder/objBasic')

        self.assertEqual(x, check)
 
    def test_hook_chain_redirect(self):
        r = self.makeBaseRequest()
        check = []
        self.f1.objBasic.traversal = [ (pt_chain_test, (r, 'a')),
                                       (pt_chain_test, (r, 'b')),
                                       (pt_chain_test, (r, 'c')),
                                       (pt_simple_redirect, (check,)),
                                       (pt_simple_redirect, (1,)),
                                       (pt_chain_test, (r, 'd'))]

        x = r.traverse('folder/objBasic')

        self.assertEqual(r.get('a',''), 'abc')
        self.assertEqual(x, check)

def test_suite():
    return TestSuite( ( makeSuite(TestBaseRequestPT), ) )

if __name__ == '__main__':
    main(defaultTest='test_suite')
