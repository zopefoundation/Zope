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
        self.assertFalse(_called)

    def test___call___w_SUPPRESS_ACCESSRULE_in_URL(self):
        # This behavior changed in landing lp:142878.
        _called = []
        def _func(*args):
            _called.append(args)
        rule = self._makeOne()
        request = DummyRequest(TraversalRequestNameStack=
                                    ['_SUPPRESS_ACCESSRULE'])
        request.steps = []
        container = DummyContainer(testing=_func)
        rule(container, request)
        self.assertTrue(_called)
        self.assertEqual(request._virtual_root, None)

    def test___call___wo_SUPPRESS_ACCESSRULE(self):
        _called = []
        def _func(*args):
            _called.append(args)
        rule = self._makeOne()
        request = DummyRequest(TraversalRequestNameStack=[])
        request.steps = []
        container = DummyContainer(testing=_func)
        rule(container, request)
        self.assertTrue(_called)
        self.assertEqual(request._virtual_root, None)


class Test_manage_addAccessRule(unittest.TestCase):

    def _callFUT(self, container, method_id, REQUEST):
        from Products.SiteAccess.AccessRule import manage_addAccessRule
        return manage_addAccessRule(container, method_id, REQUEST)

    def test_no_method_id_no_existing_rules_no_request(self):
        container = DummyContainer()
        result = self._callFUT(container, None, None)
        self.assertTrue(result is None)
        self.assertFalse(container.__dict__)

    def test_no_method_id_no_existing_rules_w_request(self):
        container = DummyContainer()
        result = self._callFUT(container, None, {'URL1': 'http://example.com/'})
        self.assertTrue(isinstance(result, str))
        self.assertTrue('<TITLE>No Access Rule</TITLE>' in result)
        self.assertFalse(container.__dict__)

    def test_no_method_id_w_existing_rules_no_request(self):
        from ZPublisher.BeforeTraverse import registerBeforeTraverse
        container = DummyContainer()
        old_rule = container.old_rule = DummyObject(name='old_rule',
                                                    icon='rule_icon.jpg')
        registerBeforeTraverse(container, old_rule, 'AccessRule')
        result = self._callFUT(container, None, None)
        self.assertTrue(result is None)
        self.assertFalse(container.__before_traverse__)
        self.assertFalse('icon' in old_rule.__dict__)

    def test_w_method_id_w_existing_rules_w_request_none(self):
        from ZPublisher.BeforeTraverse import registerBeforeTraverse
        container = DummyContainer()
        old_rule = container.old_rule = DummyObject(name='old_rule',
                                                    icon='rule_icon.jpg')
        registerBeforeTraverse(container, old_rule, 'AccessRule')
        request = DummyRequest(URL1 = 'http://example.com/')
        request.form = {'none': '1'}
        result = self._callFUT(container, None, request)
        self.assertTrue(isinstance(result, str))
        self.assertTrue('<TITLE>No Access Rule</TITLE>' in result)
        self.assertFalse(container.__before_traverse__)
        self.assertFalse('icon' in old_rule.__dict__)

    def test_w_invalid_method_id_w_existing_rules_no_request(self):
        from ZPublisher.BeforeTraverse import registerBeforeTraverse
        container = DummyContainer()
        old_rule = container.old_rule = DummyObject(name='old_rule',
                                                    icon='rule_icon.jpg')
        registerBeforeTraverse(container, old_rule, 'AccessRule')
        result = self._callFUT(container, 'nonesuch', None)
        self.assertTrue(result is None)
        self.assertTrue((99, 'AccessRule') in container.__before_traverse__)
        rule = container.__before_traverse__[(99, 'AccessRule')]
        self.assertEqual(rule.name, 'old_rule')
        self.assertEqual(old_rule.icon, 'rule_icon.jpg')

    def test_w_invalid_method_id_w_existing_rules_w_request(self):
        from ZPublisher.BeforeTraverse import registerBeforeTraverse
        container = DummyContainer()
        old_rule = container.old_rule = DummyObject(name='old_rule',
                                                    icon='rule_icon.jpg')
        registerBeforeTraverse(container, old_rule, 'AccessRule')
        request = DummyRequest(URL1 = 'http://example.com/')
        request.form = {}
        result = self._callFUT(container, 'nonesuch', request)
        self.assertTrue(isinstance(result, str))
        self.assertTrue('<TITLE>Invalid Method Id</TITLE>' in result)
        self.assertTrue((99, 'AccessRule') in container.__before_traverse__)
        rule = container.__before_traverse__[(99, 'AccessRule')]
        self.assertEqual(rule.name, 'old_rule')
        self.assertEqual(old_rule.icon, 'rule_icon.jpg')

    def test_w_valid_method_id_w_existing_rules_no_request(self):
        from ZPublisher.BeforeTraverse import registerBeforeTraverse
        container = DummyContainer()
        old_rule = container.old_rule = DummyObject(name='old_rule',
                                                    icon='rule_icon.jpg')
        new_rule = container.new_rule = DummyObject(name='new_rule')
        registerBeforeTraverse(container, old_rule, 'AccessRule')
        result = self._callFUT(container, 'new_rule', None)
        self.assertTrue(result is None)
        self.assertFalse((99, 'AccessRule') in container.__before_traverse__)
        self.assertTrue((1, 'AccessRule') in container.__before_traverse__)
        rule = container.__before_traverse__[(1, 'AccessRule')]
        self.assertEqual(rule.name, 'new_rule')
        self.assertFalse('icon' in old_rule.__dict__)
        self.assertEqual(new_rule.icon, 'misc_/SiteAccess/AccessRule.gif')

    def test_w_valid_method_id_w_existing_rules_w_request(self):
        from ZPublisher.BeforeTraverse import registerBeforeTraverse
        container = DummyContainer()
        old_rule = container.old_rule = DummyObject(name='old_rule',
                                                    icon='rule_icon.jpg')
        new_rule = container.new_rule = DummyObject(name='new_rule')
        registerBeforeTraverse(container, old_rule, 'AccessRule')
        request = DummyRequest(URL1 = 'http://example.com/')
        request.form = {}
        result = self._callFUT(container, 'new_rule', request)
        self.assertTrue(isinstance(result, str))
        self.assertTrue('<TITLE>Access Rule Set</TITLE>' in result)
        self.assertFalse((99, 'AccessRule') in container.__before_traverse__)
        self.assertTrue((1, 'AccessRule') in container.__before_traverse__)
        rule = container.__before_traverse__[(1, 'AccessRule')]
        self.assertEqual(rule.name, 'new_rule')
        self.assertFalse('icon' in old_rule.__dict__)
        self.assertEqual(new_rule.icon, 'misc_/SiteAccess/AccessRule.gif')


class Test_getAccessRule(unittest.TestCase):

    def _callFUT(self, container, REQUEST=None):
        from Products.SiteAccess.AccessRule import getAccessRule
        return getAccessRule(container, REQUEST)

    def test_no_rules(self):
        container = DummyContainer()
        self.assertEqual(self._callFUT(container), '')

    def test_w_rule_invalid(self):
        from ZPublisher.BeforeTraverse import registerBeforeTraverse
        container = DummyContainer()
        registerBeforeTraverse(container, DummyObject(), 'AccessRule')
        self.assertTrue(self._callFUT(container).startswith(
                                        'Invalid BeforeTraverse data: '))

    def test_w_rule_valid(self):
        from ZPublisher.BeforeTraverse import registerBeforeTraverse
        container = DummyContainer()
        registerBeforeTraverse(container, DummyObject(name='foo'), 'AccessRule')
        self.assertEqual(self._callFUT(container), 'foo')


class DummyRequest(dict):
    _virtual_root = None
    def setVirtualRoot(self, root):
        self._virtual_root = root


class DummyObject(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)


class DummyContainer(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def this(self):
        return self

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(AccessRuleTests),
        unittest.makeSuite(Test_manage_addAccessRule),
        unittest.makeSuite(Test_getAccessRule),
    ))

