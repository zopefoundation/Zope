##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Zope Classes
"""
import ExtensionClass, Globals, ZClass, Products
from Globals import InitializeClass

def manage_subclassableClassNames(self):
    r={}
    r.update(Products.meta_class_info)

    for data in self.aq_acquire('_getProductRegistryData')('zclasses'):
        r['%(product)s/%(id)s' % data] = '%(product)s: %(id)s' % data

    r=r.items()
    r.sort()
    return r

class ZClassOwner(ExtensionClass.Base):

    manage_addZClassForm=Globals.HTMLFile(
        'dtml/addZClass', globals(),
        default_class_='OFS.SimpleItem Item',
        CreateAFactory=1,
        zope_object=1)

    def manage_addZClass(self, id, title='', baseclasses=[],
                         meta_type='', CreateAFactory=0,
                         REQUEST=None, zope_object=0):
        "Add a ZClass"
        return ZClass.manage_addZClass(
            self, id, title, baseclasses, meta_type, CreateAFactory,
            REQUEST, zope_object=zope_object)

    manage_subclassableClassNames=manage_subclassableClassNames

InitializeClass(ZClassOwner)
