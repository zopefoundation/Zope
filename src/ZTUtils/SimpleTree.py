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
"""Simple Tree classes
"""

from Acquisition import aq_acquire

from .Tree import TreeMaker
from .Tree import TreeNode
from .Tree import b2a


class SimpleTreeNode(TreeNode):
    def branch(self):
        if self.state == 0:
            return {'link': None, 'img': '&nbsp;&nbsp;'}

        if self.state < 0:
            setst = 'expand'
            exnum = self.__parent__.expansion_number
        else:
            setst = 'collapse'
            exnum = self.expansion_number

        obid = self.id
        pre = aq_acquire(self, 'tree_pre')

        return {'link': '?%s-setstate=%s,%s,%s#%s' %
                        (pre, setst[0], exnum, obid, obid),
                'img': ''}


class SimpleTreeMaker(TreeMaker):
    '''Generate Simple Trees'''

    def __init__(self, tree_pre="tree"):
        self.tree_pre = tree_pre

    def node(self, object):
        node = SimpleTreeNode()
        node.object = object
        node.id = b2a(self.getId(object))
        return node

    def tree(self, root, expanded=None, subtree=0):
        node = TreeMaker.tree(self, root, expanded, subtree)
        if not subtree:
            node.tree_pre = self.tree_pre
            node.baseURL = root.REQUEST['BASEPATH1']
        return node
