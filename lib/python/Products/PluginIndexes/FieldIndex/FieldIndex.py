#############################################################################
# 
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

"""Simple column indices"""

__version__='$Revision: 1.6 $'[11:-2]

from Globals import Persistent
from Acquisition import Implicit
import BTree
import IOBTree
from zLOG import LOG, ERROR
from types import StringType, ListType, IntType, TupleType

from BTrees.OOBTree import OOBTree, OOSet
from BTrees.IOBTree import IOBTree
from BTrees.IIBTree import IITreeSet, IISet, union
import BTrees.Length

from Products.PluginIndexes import PluggableIndex 
from Products.PluginIndexes.common.UnIndex import UnIndex

from Globals import Persistent, DTMLFile
from Acquisition import Implicit
from OFS.History import Historical
from OFS.SimpleItem import SimpleItem


_marker = []

class FieldIndex(UnIndex,PluggableIndex.PluggableIndex, Persistent,
    Implicit, SimpleItem):
    """Field Indexes"""

    __implements__ = (PluggableIndex.PluggableIndexInterface,)

    meta_type="FieldIndex"

    manage_options= (
        {'label': 'Settings',     
         'action': 'manage_main',
         'help': ('FieldIndex','FieldIndex_Settings.stx')},
    )

    query_options = ["query","range"]

    index_html = DTMLFile('dtml/index', globals())

    manage_workspace = DTMLFile('dtml/manageFieldIndex', globals())


manage_addFieldIndexForm = DTMLFile('dtml/addFieldIndex', globals())

def manage_addFieldIndex(self, id, REQUEST=None, RESPONSE=None, URL3=None):
    """Add a field index"""
    return self.manage_addIndex(id, 'FieldIndex', extra=None, \
             REQUEST=REQUEST, RESPONSE=RESPONSE, URL1=URL3)

