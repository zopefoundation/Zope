import unittest
from OFS.FindSupport import FindSupport


class DummyItem(FindSupport):
    """ """

    def __init__(self, id):
        self.id = id

    def getId(self):
        return self.id


class DummyFolder(DummyItem, dict):

    def objectItems(self):
        return self.items()


class TestFindSupport(unittest.TestCase):

    def setUp(self):
        self.base = DummyFolder('base')
        self.base['1'] = DummyItem('1') 
        self.base['2'] = DummyItem('2') 
        self.base['3'] = DummyItem('3') 

    def test_interfaces(self):
        from OFS.interfaces import IFindSupport
        from zope.interface.verify import verifyClass

        verifyClass(IFindSupport, FindSupport)

    def test_find(self):
        self.assertEqual(self.base.ZopeFind(
            self.base, obj_ids=['1'])[0][0], '1')

    def test_find_apply(self):
        def func(obj, p):
            obj.id = 'foo' + obj.id 
        # ZopeFindAndApply does not return anything
        # but applies a function to the objects found
        self.assertFalse(self.base.ZopeFindAndApply(
            self.base, obj_ids=['2'], apply_func=func))

        self.assertEqual(self.base['1'].id, '1')
        self.assertEqual(self.base['2'].id, 'foo2')
        self.assertEqual(self.base['3'].id, '3')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestFindSupport),
        ))
