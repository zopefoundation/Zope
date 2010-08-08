import unittest

from ZTUtils import Tree

class Item:
    children = ()
    id = ''

    def __init__(self, id, children=()):
        self.id = id
        self.children = children

    def tpId(self): return self.id
    def tpValues(self): return self.children


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
        self.assert_(treeroot.object is self.root)

        i = 'b'
        for subnode in treeroot:
            self.assertEqual(len(subnode), 0)
            self.assertEqual(subnode.size, 1)
            self.assertEqual(subnode.height, 1)
            self.assertEqual(subnode.depth, 1)
            self.assertEqual(subnode.state, -1)
            self.assert_(subnode.object is self.items[i])
            i = chr(ord(i) + 1)

        expected_set = [self.items['a'], self.items['b'], self.items['c']]

        set = treeroot.flat()
        self.assertEqual(len(set), treeroot.size)
        self.assertEqual([s.object for s in set], expected_set)

        set = []
        def collect(node, set=set): set.append(node.object)
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
        self.assert_(treeroot.object is self.root)

        items = self.items
        expected_set = [items['a'], items['b'], items['d'], items['e'],
            items['c'], items['f'], items['h'], items['i'], items['g']]
        
        set = treeroot.flat()
        self.assertEqual(len(set), treeroot.size)
        self.assertEqual([s.object for s in set], expected_set)

        set = []
        def collect(node, set=set): set.append(node.object)
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
        def collect(node, set=set): set.append(node.object)
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
        self.assertFalse(encoded.find('\n') != -1)
        decodedmap = Tree.decodeExpansion(encoded)

        treeroot2 = self.tm.tree(self.root, decodedmap)

        self.assertEqual(treeroot1.size, treeroot2.size)
        self.assertEqual(len(treeroot1), len(treeroot2))

    def testEncodedExpansionIdWithDot(self):
        # Regression test for Collector issue #603
        # An encoded node ID with a first character with the first 6 bits set.
        item = Item('\xfcberbug!', (Item('b'),)) # 'uberbug!' with u-umlaut.
        treeroot1 = self.tm.tree(item)
        
        encoded = Tree.encodeExpansion(treeroot1.flat())
        decodedmap = Tree.decodeExpansion(encoded)

        treeroot2 = self.tm.tree(item, decodedmap)

        self.assertEqual(treeroot1.size, treeroot2.size)
        self.assertEqual(len(treeroot1), len(treeroot2))
    
    def testDecodeInputSizeLimit(self):
        self.assertRaises(ValueError, Tree.decodeExpansion, 'x' * 10000)
    
    def testDecodeDecompressedSizeLimit(self):
        import zlib
        from ZTUtils.Tree import b2a
        big = b2a(zlib.compress('x' * (1024*1100)))
        self.assert_(len(big) < 8192) # Must be under the input size limit
        self.assertRaises(ValueError, Tree.decodeExpansion, ':' + big)


def test_suite():
    return unittest.makeSuite(TreeTests)
