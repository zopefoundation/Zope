##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################
"""Object Reference implementation"""

__version__='$Revision: 1.3 $'[11:-2]


import sys, os, string, Globals, Acquisition
from HelpUtil import HelpBase, classobject
from HelpUtil import is_class, is_module
from Globals import HTMLFile
from urllib import quote




class ObjectItem(HelpBase, classobject):
    """ """
    __roles__=None

    hs_main=HTMLFile('objectitem', globals())

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

    hs_objectvalues__roles__=None
    def hs_objectvalues(self):
        return []

    

class ObjectRef(HelpBase):
    """ """
    __names__=None
    __roles__=None

    hs_main=HTMLFile('objectref', globals())

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
        for key in keys:
            setattr(self, key, dict[key])
        self.__names__=keys

    def hs_search_mod(self, mod, dict):
        # Root through a module for things that look like
        # createable object classes.
        hidden=('Control Panel', 'Principia Draft', 'simple item')
        for k, v in mod.__dict__.items():
            if is_class(v) and hasattr(v, 'meta_type') and \
               hasattr(v, '__ac_permissions__') and \
               (v.meta_type not in hidden):
                dict[v.meta_type]=ObjectItem(k, v)
            if is_module(v) and hasattr(v, '__path__'):
                dict=self.hs_search_mod(v, dict)
        return dict

    hs_objectvalues__roles__=None
    def hs_objectvalues(self):
        if self.__names__ is None:
            self.hs_deferred__init__()
        items=[]
        for id in self.__names__:
            items.append(getattr(self, id))
        return items

    def __getitem__(self, key):
        return self.__dict__[key].__of__(self)

