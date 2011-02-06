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
"""Object Reference implementation"""

__version__='$Revision: 1.10 $'[11:-2]

import sys
from urllib import quote

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from HelpSys.HelpUtil import classobject
from HelpSys.HelpUtil import HelpBase
from HelpSys.HelpUtil import is_class
from HelpSys.HelpUtil import is_module


class ObjectItem(HelpBase, classobject):
    """ """
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    hs_main=DTMLFile('dtml/objectitem', globals())

    hs_cicon='HelpSys/hs_dnode'
    hs_eicon='HelpSys/hs_dnode'

    def hs_id(self):
        return self._obj_.meta_type

    def hs_url(self):
        return quote(self._obj_.meta_type)

    hs_title=hs_id

    def __getattr__(self, name):
        if name in ('isDocTemp', '__call__'):
            raise AttributeError, name
        return getattr(self.__dict__['_obj_'], name)

    def get_method_list(self):
        rdict=classobject.get_method_dict(self)
        perms=self.__ac_permissions__
        mdict={}
        mlist=[]
        for p in self.__ac_permissions__:
            pname=p[0]
            fnames=p[1]
            for fname in fnames:
                if rdict.has_key(fname):
                    fn=rdict[fname]
                    fn.permission=pname
                    mdict[fname]=fn
        keys=mdict.keys()
        keys.sort()
        for key in keys:
            fn=mdict[key]
            if not hasattr(fn._obj_, '__doc__'):
                continue
            doc=fn._obj_.__doc__
            if hasattr(fn._obj_, '__class__') and \
               fn._obj_.__class__.__doc__ is doc:
                continue

            mlist.append(mdict[key])
        del rdict
        del mdict
        return mlist

    security.declarePublic('hs_objectvalues')
    def hs_objectvalues(self):
        return []

InitializeClass(ObjectItem)


class ObjectRef(HelpBase):
    """ """
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    __names__=None

    hs_main=DTMLFile('dtml/objectref', globals())

    hs_cicon='HelpSys/hs_cbook'
    hs_eicon='HelpSys/hs_obook'

    hs_id   ='ObjectRef'
    hs_title='Object Reference'
    hs_url  =hs_id

    def hs_deferred__init__(self):
        # This is necessary because we want to wait until all
        # products have been installed (imported).
        dict={}
        for k, v in sys.modules.items():
            if v is not None and k != '__builtins__':
                dict=self.hs_search_mod(v, dict)
        keys=dict.keys()
        keys.sort()
        __traceback_info__=(`dict`,)
        for key in keys:
            setattr(self, key, dict[key])
        self.__names__=keys

    def hs_search_mod(self, mod, dict):
        # Root through a module for things that look like
        # createable object classes.
        hidden=('Control Panel', 'simple item',
                'Broken Because Product is Gone')
        for k, v in mod.__dict__.items():
            if is_class(v) and hasattr(v, 'meta_type') and \
               hasattr(v, '__ac_permissions__'):
                if callable(v.meta_type):
                    meta_type=v.meta_type()
                else:
                    meta_type=v.meta_type
                if (meta_type is not None) and (meta_type not in hidden):
                    dict[meta_type]=ObjectItem(k, v)
            if is_module(v) and hasattr(v, '__path__'):
                dict=self.hs_search_mod(v, dict)
        return dict

    security.declarePublic('hs_objectvalues')
    def hs_objectvalues(self):
        if self.__names__ is None:
            self.hs_deferred__init__()
        items=[]
        for id in self.__names__:
            items.append(getattr(self, id))
        return items

    def __getitem__(self, key):
        return self.__dict__[key].__of__(self)

InitializeClass(ObjectRef)
