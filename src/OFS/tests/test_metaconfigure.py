import unittest


_marker = object()
class Test__registerClass(unittest.TestCase):

    def setUp(self):
        from zope.component.testing import setUp
        setUp()
        import OFS.metaconfigure
        import Products
        self._old_metatypes = getattr(Products, 'meta_types', _marker)
        self._old_monkies = OFS.metaconfigure._register_monkies[:]
        self._old_mt_regs = OFS.metaconfigure._meta_type_regs[:]
        # clear out registrations
        if self._old_metatypes is not _marker:
            Products.meta_types = []
        OFS.metaconfigure._register_monkies[:] = []
        OFS.metaconfigure._meta_type_regs[:] = []

    def tearDown(self):
        from zope.component.testing import tearDown
        import OFS.metaconfigure
        # restore registrations
        OFS.metaconfigure._meta_type_regs[:] = self._old_mt_regs 
        OFS.metaconfigure._register_monkies[:] = self._old_monkies 
        if self._old_metatypes is not _marker:
            import Products
            Products.meta_types = self._old_metatypes
        else:
            try:
                del Products.meta_types
            except AttributeError:
                pass
        tearDown()

    def _callFUT(self, klass, meta_type, permission,
                addview=None, icon=None, global_=False):
        from OFS.metaconfigure import _registerClass
        _registerClass(klass, meta_type, permission, addview, icon, global_)

    def _makeClass(self, ifaces=None):
        if ifaces is None:
            class Dummy(object):
                pass
        else:
            from zope.interface import implements
            class Dummy(object):
                implements(ifaces)
        return Dummy

    def _registerPermission(self, name, title=None):
        from zope.component import provideUtility
        from zope.interface import implements
        from zope.security.interfaces import IPermission
        class Perm:
            implements(IPermission)
            def __init__(self, title):
                self. title = title
        if title is None:
            title = name.capitalize()
        provideUtility(Perm(title), name=name)

    def _getRegistered(self):
        import OFS.metaconfigure
        import Products
        return (getattr(Products, 'meta_types', _marker),
                OFS.metaconfigure._register_monkies, 
                OFS.metaconfigure._meta_type_regs,
               )

    def test_minimal(self):
        klass = self._makeClass()
        self._registerPermission('perm')

        self._callFUT(klass, 'Dummy', 'perm')

        self.assertEqual(klass.meta_type, 'Dummy')
        mt, monkies, mt_regs = self._getRegistered()
        self.assertEqual(len(mt), 1)
        self.assertEqual(mt[0]['name'], 'Dummy')
        self.assertEqual(mt[0]['action'], '')
        self.assertEqual(mt[0]['product'], 'OFS') # XXX why?
        self.assertEqual(mt[0]['permission'], 'Perm')
        self.assertEqual(mt[0]['visibility'], None)
        self.assertEqual(mt[0]['interfaces'], ())
        self.assertEqual(mt[0]['instance'], klass)
        self.assertEqual(mt[0]['container_filter'], None)

    def test_w_icon(self):
        klass = self._makeClass()
        self._registerPermission('perm')

        self._callFUT(klass, 'Dummy', 'perm', icon='dummy.png')
        self.assertEqual(klass.icon, '++resource++dummy.png')

    def test_w_global_(self):
        klass = self._makeClass()
        self._registerPermission('perm')

        self._callFUT(klass, 'Dummy', 'perm', global_=True)

        mt, monkies, mt_regs = self._getRegistered()
        self.assertEqual(len(mt), 1)
        self.assertEqual(mt[0]['visibility'], 'Global')

    def test_w_addview(self):
        klass = self._makeClass()
        self._registerPermission('perm')

        self._callFUT(klass, 'Dummy', 'perm', 'adddummy')

        mt, monkies, mt_regs = self._getRegistered()
        self.assertEqual(len(mt), 1)
        self.assertEqual(mt[0]['action'], '+/adddummy')

    def test_w_interfaces(self):
        from zope.interface import Interface
        class IDummy(Interface):
            pass
        klass = self._makeClass((IDummy,))
        self._registerPermission('perm')

        self._callFUT(klass, 'Dummy', 'perm')

        mt, monkies, mt_regs = self._getRegistered()
        self.assertEqual(len(mt), 1)
        self.assertEqual(mt[0]['interfaces'], (IDummy,))

    def test_minimal_no_Products_metatypes(self):
        import Products
        try:
            del Products.meta_types
        except AttributeError:
            pass

        klass = self._makeClass()
        self._registerPermission('perm')

        self._callFUT(klass, 'Dummy', 'perm')

        self.assertEqual(klass.meta_type, 'Dummy')
        mt, monkies, mt_regs = self._getRegistered()
        self.assertEqual(len(mt), 1)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Test__registerClass),
    ))
