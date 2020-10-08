import unittest

from ZTUtils import Tree


class Item:
    children = ()
    id = ''

    def __init__(self, id, children=()):
        self.id = id
        self.children = children

    def tpId(self):
        return self.id

    def tpValues(self):
        return self.children


class Test_TreeNode(unittest.TestCase):

    def _getTargetClass(self):
        from ZTUtils.Tree import TreeNode
        return TreeNode

    def _makeOne(self):
        return self._getTargetClass()()

    def test_ctor(self):
        node = self._makeOne()
        self.assertEqual(len(node), 0)
        self.assertEqual(node.state, 0)
        self.assertEqual(node.height, 1)
        self.assertEqual(node.size, 1)

    def test__add_child(self):
        node = self._makeOne()
        child = self._makeOne()
        grand = self._makeOne()
        child._add_child(grand)
        node._add_child(child)
        self.assertEqual(child.height, 2)
        self.assertEqual(child.size, 2)
        self.assertEqual(len(child), 1)
        self.assertEqual(node.height, 3)
        self.assertEqual(node.size, 3)
        self.assertEqual(len(node), 1)

    def test_flat_empty(self):
        node = self._makeOne()
        flat = node.flat()
        self.assertEqual(flat, [node])

    def test_flat_non_empty(self):
        node = self._makeOne()
        child = self._makeOne()
        grand = self._makeOne()
        child._add_child(grand)
        node._add_child(child)
        flat = node.flat()
        self.assertEqual(len(flat), 3)
        self.assertIs(flat[0], node)
        self.assertIs(flat[1].aq_self, child)
        self.assertIs(flat[2].aq_self, grand)

    def test_walk_empty(self):
        node = self._makeOne()
        _called_with = []

        def _func(a_node, data=None):
            _called_with.append((a_node, data))

        node.walk(_func)
        self.assertEqual(_called_with, [(node, None)])

    def test_walk_nonempty_w_data(self):
        node = self._makeOne()
        child = self._makeOne()
        node._add_child(child)
        grand = self._makeOne()
        child._add_child(grand)
        _called_with = []
        datum = object()

        def _func(a_node, data):
            _called_with.append((a_node, data))

        node.walk(_func, datum)
        self.assertEqual(
            _called_with,
            [(node, datum), (child, datum), (grand, datum)])

    def test___getitem___empty(self):
        node = self._makeOne()
        with self.assertRaises(IndexError):
            node[0]

    def test___getitem___non_empty(self):
        node = self._makeOne()
        child = self._makeOne()
        node._add_child(child)
        found = node[0]
        self.assertIs(found.aq_self, child)


class Test_TreeMaker(unittest.TestCase):

    def _getTargetClass(self):
        from ZTUtils.Tree import TreeMaker
        return TreeMaker

    def _makeOne(self):
        return self._getTargetClass()()

    def test_ctor(self):
        maker = self._makeOne()
        self.assertEqual(maker._id, 'tpId')
        self.assertFalse(maker._assume_children)
        self.assertTrue(maker._expand_root)
        self.assertEqual(maker._values, 'tpValues')
        self.assertIsNone(maker._values_filter)
        self.assertIsNone(maker._values_function)
        self.assertIsNone(maker._state_function)
        self.assertIsNone(maker._cached_children)

    def test_setIdAttr(self):
        maker = self._makeOne()
        maker.setIdAttr('foo')
        self.assertEqual(maker._id, 'foo')

    def test_setAssumeChildren(self):
        maker = self._makeOne()
        maker.setAssumeChildren(True)
        self.assertTrue(maker._assume_children)

    def test_setExpandRoot(self):
        maker = self._makeOne()
        maker.setExpandRoot(False)
        self.assertFalse(maker._expand_root)

    def test_setChildAccess_w_attrname(self):
        maker = self._makeOne()
        maker.setChildAccess(attrname='foo')
        self.assertEqual(maker._values, 'foo')
        self.assertIsNone(maker._values_filter)
        self.assertIsNone(maker._values_function)

    def test_setChildAccess_w_filter(self):

        def _filter(obj):
            pass

        maker = self._makeOne()
        maker.setChildAccess(filter=_filter)
        self.assertEqual(maker._values, 'tpValues')
        self.assertIs(maker._values_filter, _filter)
        self.assertIsNone(maker._values_function)

    def test_setChildAccess_w_attrname_and_filter(self):

        def _filter(obj):
            pass

        maker = self._makeOne()
        maker.setChildAccess(attrname='foo', filter=_filter)
        self.assertEqual(maker._values, 'foo')
        self.assertIs(maker._values_filter, _filter)
        self.assertIsNone(maker._values_function)

    def test_setChildAccess_w_func(self):

        def _func(obj):
            pass

        maker = self._makeOne()
        maker.setChildAccess(function=_func)
        self.assertEqual(maker._values, 'tpValues')
        self.assertIsNone(maker._values_filter)
        self.assertIs(maker._values_function, _func)

    def test_setStateFunction(self):
        maker = self._makeOne()

        def _func(obj):
            pass

        maker.setStateFunction(_func)
        self.assertIs(maker._state_function, _func)

    def test_getId_obj_has_simple_attr(self):

        class Obj:
            tpId = 'foo'

        maker = self._makeOne()
        self.assertEqual(maker.getId(Obj()), 'foo')

    def test_getId_obj_has_method(self):

        class Obj:

            def tpId(self):
                return 'foo'

        maker = self._makeOne()
        self.assertEqual(maker.getId(Obj()), 'foo')

    def test_getId_obj_has__p_oid(self):

        class Obj:
            _p_oid = 123

        maker = self._makeOne()
        self.assertEqual(maker.getId(Obj()), '123')

    def test_getId_obj_fallback_to_id(self):
        obj = object()
        maker = self._makeOne()
        self.assertEqual(maker.getId(obj), id(obj))


class Test_b2a(unittest.TestCase):

    def _callFUT(self, value):
        from ZTUtils.Tree import b2a
        return b2a(value)

    def test_w_native_str(self):
        import base64
        for value, expected in [
            (b'', b''),
            (b'abc', b'abc'),
            (b'abc+def', b'abc+def'),
        ]:
            self.assertEqual(
                self._callFUT(value), base64.urlsafe_b64encode(expected))


class TreeTests(unittest.TestCase):
    def setUp(self):
        self.tm = Tree.TreeMaker()
        self.root = Item('a', (
            Item('b', (
                Item('d'), Item('e'))),
            Item('c', (
                Item('f', (
                    Item('h'), Item('i'))),
                Item('g')))))

        self.items = {
            'a': self.root,
            'b': self.root.children[0],
            'c': self.root.children[1],
            'd': self.root.children[0].children[0],
            'e': self.root.children[0].children[1],
            'f': self.root.children[1].children[0],
            'g': self.root.children[1].children[1],
            'h': self.root.children[1].children[0].children[0],
            'i': self.root.children[1].children[0].children[1],
        }

        self.expansionmap = {Tree.b2a('a'): {Tree.b2a('c'): None}}

    def testBaseTree(self):
        treeroot = self.tm.tree(self.root)

        self.assertEqual(len(treeroot), 2)
        self.assertEqual(treeroot.size, 3)
        self.assertEqual(treeroot.height, 2)
        self.assertEqual(treeroot.depth, 0)
        self.assertEqual(treeroot.state, 1)
        self.assertTrue(treeroot.object is self.root)

        i = 'b'
        for subnode in treeroot:
            self.assertEqual(len(subnode), 0)
            self.assertEqual(subnode.size, 1)
            self.assertEqual(subnode.height, 1)
            self.assertEqual(subnode.depth, 1)
            self.assertEqual(subnode.state, -1)
            self.assertTrue(subnode.object is self.items[i])
            i = chr(ord(i) + 1)

        expected_set = [self.items['a'], self.items['b'], self.items['c']]

        set = treeroot.flat()
        self.assertEqual(len(set), treeroot.size)
        self.assertEqual([s.object for s in set], expected_set)

        set = []

        def collect(node, set=set):
            set.append(node.object)

        treeroot.walk(collect)
        self.assertEqual(len(set), treeroot.size)
        self.assertEqual(set, expected_set)

    def testExpandedTree(self):
        treeroot = self.tm.tree(self.root, 1)

        self.assertEqual(len(treeroot), 2)
        self.assertEqual(treeroot.size, len(self.items))
        self.assertEqual(treeroot.height, 4)
        self.assertEqual(treeroot.depth, 0)
        self.assertEqual(treeroot.state, 1)
        self.assertTrue(treeroot.object is self.root)

        items = self.items
        expected_set = [
            items['a'], items['b'], items['d'], items['e'],
            items['c'], items['f'], items['h'], items['i'], items['g']]

        set = treeroot.flat()
        self.assertEqual(len(set), treeroot.size)
        self.assertEqual([s.object for s in set], expected_set)

        set = []

        def collect(node, set=set):
            set.append(node.object)

        treeroot.walk(collect)
        self.assertEqual(len(set), treeroot.size)
        self.assertEqual(set, expected_set)

        leaves = ('d', 'e', 'g', 'h', 'i')
        for node in treeroot.flat():
            if node.object.id in leaves:
                self.assertEqual(node.state, 0)
            else:
                self.assertEqual(node.state, 1)

            self.assertEqual(node.size, len(node.flat()))

    def testExpansionMap(self):
        treeroot = self.tm.tree(self.root, self.expansionmap)

        self.assertEqual(treeroot.size, 5)
        self.assertEqual(treeroot.state, 1)
        self.assertEqual(treeroot[0].state, -1)
        self.assertEqual(treeroot[1].state, 1)
        self.assertEqual(treeroot[1][0].state, -1)
        self.assertEqual(treeroot[1][1].state, 0)

    def testAssumeChildren(self):
        self.tm.setAssumeChildren(True)
        treeroot = self.tm.tree(self.root, self.expansionmap)
        self.assertEqual(treeroot[1][1].state, -1)

    def testNoExpandRoot(self):
        self.tm.setExpandRoot(False)
        treeroot = self.tm.tree(self.root)

        self.assertEqual(treeroot.state, -1)
        self.assertEqual(len(treeroot), 0)

    def testIdAttribute(self):
        treeroot = self.tm.tree(self.root)
        self.tm.setIdAttr('id')
        treeroot2 = self.tm.tree(self.root)

        self.assertEqual(treeroot.id, treeroot2.id)

    def testChildrenAttribute(self):
        self.tm.setChildAccess(attrname='children')
        treeroot = self.tm.tree(self.root)

        self.assertEqual(len(treeroot), 2)

    def testChildrenFilter(self):
        def filter(children):
            return [c for c in children if c.id in ('b', 'd')]

        self.tm.setChildAccess(filter=filter)
        treeroot = self.tm.tree(self.root, 1)

        self.assertEqual(treeroot.size, 3)
        self.assertEqual(len(treeroot), 1)
        self.assertEqual(len(treeroot[0]), 1)

        expected_set = [self.items['a'], self.items['b'], self.items['d']]
        set = []

        def collect(node, set=set):
            set.append(node.object)

        treeroot.walk(collect)
        self.assertEqual(set, expected_set)

    def testChildrenFunction(self):
        def childrenFunction(object):
            return object.children

        self.tm.setChildAccess(function=childrenFunction)
        treeroot = self.tm.tree(self.root)

        self.assertEqual(len(treeroot), 2)

    def testStateFunction(self):
        def stateFunction(object, state):
            if object.id == 'b':
                return 1
            if object.id == 'd':
                return -1
            return state

        self.tm.setStateFunction(stateFunction)
        treeroot = self.tm.tree(self.root)

        self.assertEqual(treeroot.size, 5)
        self.assertEqual(treeroot.state, 1)
        self.assertEqual(treeroot[0].state, 1)
        self.assertEqual(treeroot[0][0].state, -1)
        self.assertEqual(treeroot[0][1].state, 0)
        self.assertEqual(treeroot[1].state, -1)

    def testEncodeDecode(self):
        treeroot1 = self.tm.tree(self.root, self.expansionmap)

        encoded = Tree.encodeExpansion(treeroot1.flat())
        self.assertFalse(encoded.find(b'\n') != -1)
        decodedmap = Tree.decodeExpansion(encoded)

        treeroot2 = self.tm.tree(self.root, decodedmap)

        self.assertEqual(treeroot1.size, treeroot2.size)
        self.assertEqual(len(treeroot1), len(treeroot2))

    def testEncodedExpansionIdWithDot(self):
        # Regression test for Collector issue #603
        # An encoded node ID with a first character with the first 6 bits set.
        item = Item('\xfcberbug!', (Item('b'),))  # 'uberbug!' with u-umlaut.
        treeroot1 = self.tm.tree(item)

        encoded = Tree.encodeExpansion(treeroot1.flat())
        decodedmap = Tree.decodeExpansion(encoded)

        treeroot2 = self.tm.tree(item, decodedmap)

        self.assertEqual(treeroot1.size, treeroot2.size)
        self.assertEqual(len(treeroot1), len(treeroot2))

    def testDecodeInputSizeLimit(self):
        with self.assertRaises(ValueError):
            Tree.decodeExpansion(b'x' * 10000)

    def testDecodeDecompressedSizeLimit(self):
        import zlib

        from ZTUtils.Tree import b2a
        big = b2a(zlib.compress(b'x' * (1024 * 1100)))
        self.assertTrue(len(big) < 8192)  # Must be under the input size limit
        with self.assertRaises(ValueError):
            Tree.decodeExpansion(b':' + big)
