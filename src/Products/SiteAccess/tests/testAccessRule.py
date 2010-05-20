import unittest


class AccessRuleTests(unittest.TestCase):

    _old_SAR = None

    def setUp(self):
        from Testing.ZopeTestCase import ZopeLite
        ZopeLite.startup()

    def tearDown(self):
        if self._old_SAR is not None:
            self._set_SUPPRESS_ACCESSRULE(self._old_SAR)

    def _set_SUPPRESS_ACCESSRULE(self, value):
        from Products.SiteAccess import AccessRule as AR
        (self._old_SAR,
         AR.SUPPRESS_ACCESSRULE) = (AR.SUPPRESS_ACCESSRULE, value)

    def _getTargetClass(self):
        from Products.SiteAccess.AccessRule import AccessRule
        return AccessRule

    def _makeOne(self, method_id='testing'):
        return self._getTargetClass()(method_id)

    def test___call___w_SUPPRESS_ACCESSRULE_set(self):
        self._set_SUPPRESS_ACCESSRULE(1)
        _called = []
        def _func(*args):
            _called.append(args)
        rule = self._makeOne()
        request = DummyRequest(TraversalRequestNameStack=[])
        container = DummyContainer(testing=_func)
        rule(container, request)
        self.failIf(_called)

    def test___call___w_SUPPRESS_ACCESSRULE_in_URL(self):
        # This behavior will change once we land lp:142878.
        _called = []
        def _func(*args):
            _called.append(args)
        rule = self._makeOne()
        request = DummyRequest(TraversalRequestNameStack=
                                    ['_SUPPRESS_ACCESSRULE'])
        request.steps = []
        container = DummyContainer(testing=_func)
        rule(container, request)
        self.failIf(_called)
        self.assertEqual(request._virtual_root, ['_SUPPRESS_ACCESSRULE'])

    def test___call___wo_SUPPRESS_ACCESSRULE(self):
        _called = []
        def _func(*args):
            _called.append(args)
        rule = self._makeOne()
        request = DummyRequest(TraversalRequestNameStack=[])
        request.steps = []
        container = DummyContainer(testing=_func)
        rule(container, request)
        self.failUnless(_called)
        self.assertEqual(request._virtual_root, None)


class DummyRequest(dict):
    _virtual_root = None
    def setVirtualRoot(self, root):
        self._virtual_root = root

class DummyContainer(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(AccessRuleTests),
    ))

