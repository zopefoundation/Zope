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
from App.class_init import default__class_init__ as InitializeClass
from App.special_dtml import HTMLFile
from ExtensionClass import Base


def manage_subclassableClassNames(self):
    import Products
    r={}
    r.update(Products.meta_class_info)

    for data in self.aq_acquire('_getProductRegistryData')('zclasses'):
        r['%(product)s/%(id)s' % data] = '%(product)s: %(id)s' % data

    r=r.items()
    r.sort()
    return r

class ZClassOwner(Base):

    manage_addZClassForm=HTMLFile(
        'dtml/addZClass', globals(),
        default_class_='OFS.SimpleItem Item',
        CreateAFactory=1,
        zope_object=1)

    def manage_addZClass(self, id, title='', baseclasses=[],
                         meta_type='', CreateAFactory=0,
                         REQUEST=None, zope_object=0):
        "Add a ZClass"
        from ZClasses.ZClass import manage_addZClass
        return manage_addZClass(
            self, id, title, baseclasses, meta_type, CreateAFactory,
            REQUEST, zope_object=zope_object)

    manage_subclassableClassNames=manage_subclassableClassNames

InitializeClass(ZClassOwner)
