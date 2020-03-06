##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Tree manipulation classes
"""

import base64
import zlib

from Acquisition import Explicit
from ComputedAttribute import ComputedAttribute


class TreeNode(Explicit):
    __allow_access_to_unprotected_subobjects__ = 1
    state = 0  # leaf
    height = 1
    size = 1

    def __init__(self):
        self._child_list = []

    def _add_child(self, child):
        'Add a child which already has all of its children.'
        self._child_list.append(child)
        self.height = max(self.height, child.height + 1)
        self.size = self.size + child.size

    def flat(self):
        'Return a flattened preorder list of tree nodes'
        items = []
        self.walk(items.append)
        return items

    def walk(self, f, data=None):
        'Preorder walk this tree, passing each node to a function'
        if data is None:
            f(self)
        else:
            f(self, data)
        for child in self._child_list:
            child.__of__(self).walk(f, data)

    def _depth(self):
        return self.__parent__.depth + 1

    depth = ComputedAttribute(_depth, 1)

    def __getitem__(self, index):
        return self._child_list[index].__of__(self)

    def __len__(self):
        return len(self._child_list)


_marker = []


class TreeMaker:
    '''Class for mapping a hierarchy of objects into a tree of nodes.'''

    __allow_access_to_unprotected_subobjects__ = 1

    _id = 'tpId'
    _assume_children = False
    _expand_root = True
    _values = 'tpValues'
    _values_filter = None
    _values_function = None
    _state_function = None

    _cached_children = None

    def setIdAttr(self, id):
        """Set the attribute or method name called to get a unique Id.

        The id attribute or method is used to get a unique id for every
        node in the tree, so that the state of the tree can be encoded
        as a string using Tree.encodeExpansion(). The returned id should
        be unique and stable across Zope requests.

        If the attribute or method isn't found on an object, either
        the objects persistence Id or the result of id() on the object
        is used instead.
        """
        self._id = id

    def setExpandRoot(self, expand):
        """Set wether or not to expand the root node by default.

        When no expanded flag or mapping is passed to .tree(), assume the root
        node is expanded, and leave all subnodes closed.

        The default is to expand the root node.
        """
        self._expand_root = expand and True or False

    def setAssumeChildren(self, assume):
        """Set wether or not to assume nodes have children.

        When a node is not expanded, when assume children is set, don't
        determine if it is a leaf node, but assume it can be opened. Use this
        when determining the children for a node is expensive.

        The default is to not assume there are children.
        """
        self._assume_children = assume and True or False

    def setChildAccess(self, attrname=_marker, filter=_marker,
                       function=_marker):
        '''Set the criteria for fetching child nodes.

        Child nodes can be accessed through either an attribute name
        or callback function.  Children fetched by attribute name can
        be filtered through a callback function.
        '''
        if function is _marker:
            self._values_function = None
            if attrname is not _marker:
                self._values = str(attrname)
            if filter is not _marker:
                self._values_filter = filter
        else:
            self._values_function = function

    def setStateFunction(self, function):
        """Set the expansion state function.

        This function will be called to determine if a node should be open or
        collapsed, or should be treated as a leaf node. The function is passed
        the current object, and the intended state for that object. It should
        return the actual state the object should be in. State is encoded as an
        integer, meaning:

            -1: Node closed. Children will not be processed.
             0: Leaf node, cannot be opened or closed, no children are
                processed.
             1: Node opened. Children will be processed as part of the tree.
        """
        self._state_function = function

    def getId(self, object):
        id_attr = self._id
        if hasattr(object, id_attr):
            obid = getattr(object, id_attr)
            if not simple_type(obid):
                obid = obid()
            return obid
        if hasattr(object, '_p_oid'):
            return str(object._p_oid)
        return id(object)

    def node(self, object):
        node = TreeNode()
        node.object = object
        node.id = b2a(self.getId(object))
        return node

    def hasChildren(self, object):
        if self._assume_children:
            return 1
        # Cache generated children for a subsequent call to getChildren
        self._cached_children = (object, self.getChildren(object))
        return not not self._cached_children[1]

    def filterChildren(self, children):
        if self._values_filter:
            return self._values_filter(children)
        return children

    def getChildren(self, object):
        # Check and clear cache first
        if self._cached_children is not None:
            ob, children = self._cached_children
            self._cached_children = None
            if ob is object:
                return children

        if self._values_function is not None:
            return self._values_function(object)

        children = getattr(object, self._values)
        if not isinstance(children, (list, tuple)):
            # Assume callable; result not useful anyway otherwise.
            children = children()

        return self.filterChildren(children)

    def tree(self, root, expanded=None, subtree=0):
        '''Create a tree from root, with specified nodes expanded.

        "expanded" must be false, true, or a mapping.
        Each key of the mapping is the id of a top-level expanded
        node, and each value is the "expanded" value for the
        children of that node.
        '''
        node = self.node(root)
        child_exp = expanded
        if not simple_type(expanded):
            # Assume a mapping
            expanded = node.id in expanded
            child_exp = child_exp.get(node.id)

        expanded = expanded or (not subtree and self._expand_root)
        # Set state to 0 (leaf), 1 (opened), or -1 (closed)
        state = self.hasChildren(root) and (expanded or -1)
        if self._state_function is not None:
            state = self._state_function(node.object, state)
        node.state = state
        if state > 0:
            for child in self.getChildren(root):
                node._add_child(self.tree(child, child_exp, 1))

        if not subtree:
            node.depth = 0
        return node


_SIMPLE_TYPES = {type(''), type(b''), type(0), type(0.0), type(None)}


def simple_type(ob):
    return type(ob) in _SIMPLE_TYPES


def b2a(s):
    '''Encode a bytes/string as a cookie- and url-safe string.

    Encoded string use only alphanumeric characters, and "._-".
    '''
    if not isinstance(s, bytes):
        s = str(s)
        if isinstance(s, str):
            s = s.encode('utf-8')
    return base64.urlsafe_b64encode(s)


def a2b(s):
    '''Decode a b2a-encoded value to bytes.'''
    if not isinstance(s, bytes):
        if isinstance(s, str):
            s = s.encode('ascii')
    return base64.urlsafe_b64decode(s)


def encodeExpansion(nodes, compress=1):
    '''Encode the expanded node ids of a tree into bytes.

    Accepts a list of nodes, such as that produced by root.flat().
    Marks each expanded node with an expansion_number attribute.
    Since node ids are encoded, the resulting string is safe for
    use in cookies and URLs.
    '''
    steps = []
    last_depth = -1
    for n, node in enumerate(nodes):
        if node.state <= 0:
            continue
        dd = last_depth - node.depth + 1
        last_depth = node.depth
        if dd > 0:
            steps.append('_' * dd)
        steps.append(node.id)  # id is bytes
        node.expansion_number = n
    result = b':'.join(steps)
    if compress and len(result) > 2:
        zresult = b':' + b2a(zlib.compress(result, 9))
        if len(zresult) < len(result):
            result = zresult
    return result


def decodeExpansion(s, nth=None, maxsize=8192):
    '''Decode an expanded node map from bytes.

    If nth is an integer, also return the (map, key) pair for the nth entry.
    '''
    if len(s) > maxsize:  # Set limit to avoid DoS attacks.
        raise ValueError('Encoded node map too large')

    if s.startswith(b':'):  # Compressed state
        dec = zlib.decompressobj()
        s = dec.decompress(a2b(s[1:]), maxsize)
        if dec.unconsumed_tail:
            raise ValueError('Encoded node map too large')
        del dec

    map = m = {}
    mstack = []
    pop = 0
    nth_pair = None
    if nth is not None:
        nth_pair = (None, None)
    obid = None
    for step in s.split(b':'):
        if step.startswith(b'_'):
            pop = len(step) - 1
            continue
        if pop < 0:
            mstack.append(m)
            m[obid] = {}
            m = m[obid]
        elif map:
            m[obid] = None
        if len(step) == 0:
            return map
        obid = step
        if pop > 0:
            m = mstack[-pop]
            del mstack[-pop:]
        pop = -1
        if nth == 0:
            nth_pair = (m, obid)
            nth = None
        elif nth is not None:
            nth = nth - 1
    m[obid] = None
    if nth == 0:
        return map, (m, obid)
    if nth_pair is not None:
        return map, nth_pair
    return map
