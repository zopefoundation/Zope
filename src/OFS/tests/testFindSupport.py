import unittest

from OFS.FindSupport import FindSupport


class DummyItem(FindSupport):
    """ """

    def __init__(self, id, text=''):
        self.id = id
        self.text = text

    def getId(self):
        return self.id

    def PrincipiaSearchSource(self):
        return self.text


class DummyFolder(DummyItem, dict):

    def objectItems(self):
        return list(self.items())


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

    def test_find_text(self):
        # Make sure ZopeFind can handle normal text
        findme = 'findme'
        self.base['doc1'] = DummyItem('doc1', text=findme)
        self.base['doc2'] = DummyItem('doc2', text=findme)

        res = self.base.ZopeFind(self.base, obj_searchterm=findme)
        self.assertEqual(len(res), 2)
        self.assertEqual({x[0] for x in res}, {'doc1', 'doc2'})

    def test_find_text_nonascii(self):
        # Make sure ZopeFind can handle text and encoded text (binary) data
        unencoded = '\xfcml\xe4\xfct'
        encoded = '\xfcml\xe4\xfct'.encode()
        self.base['text'] = DummyItem('text', text=unencoded)
        self.base['bytes'] = DummyItem('bytes', text=encoded)

        res = self.base.ZopeFind(self.base, obj_searchterm=unencoded)
        self.assertEqual(len(res), 2)
        self.assertEqual({x[0] for x in res}, {'text', 'bytes'})

    def test_find_text_nondecodable(self):
        # Make sure ZopeFind does not crash searching text in nondecodable data
        encoded = b'\xf6'
        self.base['bytes'] = DummyItem('bytes', text=encoded)

        def SearchableText():
            return encoded
        st_item = DummyItem('text')
        st_item.SearchableText = SearchableText
        self.base['text'] = st_item
        try:
            self.base.ZopeFind(self.base, obj_searchterm='anything')
        except UnicodeDecodeError:  # pragma: no cover
            self.fail('ZopeFind in undecodable data raises UnicodeDecodeError')

    def test_find_text_tainted(self):
        # Make sure ZopeFind can handle "Tainted" text for searches
        # Tainted strings are created when the publisher sees what appears
        # to be HTML code in the input, e.g. when you enter a HTML tag into
        # the Find tab form in "containing"
        from AccessControl.tainted import TaintedBytes
        from AccessControl.tainted import TaintedString

        findme = 'findme'
        self.base['doc1'] = DummyItem('doc1', text=findme)
        self.base['doc2'] = DummyItem('doc2', text=findme)

        tainted_string = TaintedString(findme)
        res = self.base.ZopeFind(self.base, obj_searchterm=tainted_string)
        self.assertEqual(len(res), 2)
        self.assertEqual({x[0] for x in res}, {'doc1', 'doc2'})

        tainted_bytes = TaintedBytes(bytes(findme, 'latin-1'))
        res = self.base.ZopeFind(self.base, obj_searchterm=tainted_bytes)
        self.assertEqual(len(res), 2)
        self.assertEqual({x[0] for x in res}, {'doc1', 'doc2'})
