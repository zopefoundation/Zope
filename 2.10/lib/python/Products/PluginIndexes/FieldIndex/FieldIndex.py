##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Simple column indices.

$Id$
"""

from Globals import DTMLFile

from Products.PluginIndexes.common.UnIndex import UnIndex


class FieldIndex(UnIndex):

    """Index for simple fields.
    """

    __implements__ = UnIndex.__implements__

    meta_type="FieldIndex"

    manage_options= (
        {'label': 'Settings',
         'action': 'manage_main',
         'help': ('FieldIndex','FieldIndex_Settings.stx')},
        {'label': 'Browse',
         'action': 'manage_browse',
         'help': ('FieldIndex','FieldIndex_Settings.stx')},
    )

    query_options = ["query","range"]

    manage = manage_main = DTMLFile('dtml/manageFieldIndex', globals())
    manage_main._setName('manage_main')
    manage_browse = DTMLFile('../dtml/browseIndex', globals())


manage_addFieldIndexForm = DTMLFile('dtml/addFieldIndex', globals())

def manage_addFieldIndex(self, id, extra=None,
                REQUEST=None, RESPONSE=None, URL3=None):
    """Add a field index"""
    return self.manage_addIndex(id, 'FieldIndex', extra=extra, \
             REQUEST=REQUEST, RESPONSE=RESPONSE, URL1=URL3)
