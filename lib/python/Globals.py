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

"""Global definitions"""

__version__='$Revision: 1.33 $'[11:-2]

import sys, os
from DateTime import DateTime
from string import atof, rfind
import Acquisition
DevelopmentMode=None

def package_home(globals_dict):
    __name__=globals_dict['__name__']
    m=sys.modules[__name__]
    if hasattr(m,'__path__'): return m.__path__[0]
    return sys.modules[__name__[:rfind(__name__,'.')]].__path__[0]

try: home=os.environ['SOFTWARE_HOME']
except:
    import Products
    home=package_home(Products.__dict__)
    if not os.path.isabs(home):
        home=os.path.join(os.getcwd(), home)
        
    home,e=os.path.split(home)
    if os.path.split(home)[1]=='.': home=os.path.split(home)[0]
    if os.path.split(home)[1]=='..':
        home=os.path.split(os.path.split(home)[0])[0]

SOFTWARE_HOME=sys.modules['__builtin__'].SOFTWARE_HOME=home

try: chome=os.environ['INSTANCE_HOME']
except:
    chome=home
    d,e=os.path.split(chome)
    if e=='python':
        d,e=os.path.split(d)
        if e=='lib': chome=d or os.getcwd()
    
INSTANCE_HOME=sys.modules['__builtin__'].INSTANCE_HOME=chome


from BoboPOS import Persistent, PickleDictionary
import BoboPOS.PersistentMapping
sys.modules['PersistentMapping']=BoboPOS.PersistentMapping # hack for bw comp
from BoboPOS.PersistentMapping import PersistentMapping

import DocumentTemplate, MethodObject
from AccessControl.PermissionRole import PermissionRole

class ApplicationDefaultPermissions:
    _View_Permission='Manager', 'Anonymous'
    
def default__class_init__(self):
    dict=self.__dict__
    have=dict.has_key
    ft=type(default__class_init__)
    for name, v in dict.items():
        if hasattr(v,'_need__name__') and v._need__name__:
            v.__dict__['__name__']=name
            if name=='manage' or name[:7]=='manage_':
                name=name+'__roles__'
                if not have(name): dict[name]='Manager',
        elif name=='manage' or name[:7]=='manage_' and type(v) is ft:
            name=name+'__roles__'
            if not have(name): dict[name]='Manager',

    if hasattr(self, '__ac_permissions__'):
        for acp in self.__ac_permissions__:
            pname, mnames = acp[:2]
            pr=PermissionRole(pname)
            for mname in mnames:
                try: getattr(self, mname).__roles__=pr
                except: dict[mname+'__roles__']=pr
            pname=pr._p
            if not hasattr(ApplicationDefaultPermissions, pname):
                if len(acp) > 2:
                    setattr(ApplicationDefaultPermissions, pname, acp[2])
                else:
                    setattr(ApplicationDefaultPermissions, pname, ('Manager',))

Persistent.__dict__['__class_init__']=default__class_init__

class PersistentUtil:

    def bobobase_modification_time(self):
        try:
            t=self._p_mtime
            if t is None: return DateTime()
        except: t=0
        return DateTime(t)

    def locked_in_session(self):
        oid=self._p_oid
        return (oid and SessionBase.locks.has_key(oid)
                and SessionBase.verify_lock(oid))

    def modified_in_session(self):
        jar=self._p_jar
        if jar is None:
            if hasattr(self,'aq_parent') and hasattr(self.aq_parent, '_p_jar'):
                jar=self.aq_parent._p_jar
            if jar is None: return 0
        if not jar.name: return 0
        try: jar.db[self._p_oid]
        except: return 0
        return 1

for k, v in PersistentUtil.__dict__.items(): Persistent.__dict__[k]=v
    



class HTML(DocumentTemplate.HTML,Persistent,):
    "Persistent HTML Document Templates"

class HTMLDefault(DocumentTemplate.HTMLDefault,Persistent,):
    "Persistent Default HTML Document Templates"

class HTMLFile(DocumentTemplate.HTMLFile,MethodObject.Method,):
    "Persistent HTML Document Templates read from files"

    class func_code: pass
    func_code=func_code()
    func_code.co_varnames='trueself', 'self', 'REQUEST'
    func_code.co_argcount=3
    _need__name__=1
    _v_last_read=0

    def __init__(self,name,_prefix=None, **kw):
        if _prefix is None: _prefix=SOFTWARE_HOME
        elif type(_prefix) is not type(''): _prefix=package_home(_prefix)

        args=(self, '%s/%s.dtml' % (_prefix,name))
        apply(HTMLFile.inheritedAttribute('__init__'),args,kw)

    def __call__(self, *args, **kw):
        if DevelopmentMode:
            t=os.stat(self.raw)
            if t != self._v_last_read:
                self.cook()
                self._v_last_read=t
        return apply(HTMLFile.inheritedAttribute('__call__'),
                     (self,)+args[1:],kw)

data_dir     = INSTANCE_HOME+'/var'
BobobaseName = '%s/Data.bbb' % data_dir

from App.Dialogs import MessageDialog

SessionNameName='Principia-Session'
    
# utility stuff

def attrget(o,name,default):
    if hasattr(o,name): return getattr(o,name)
    return default

class Selector:
    def __init__(self, key):
        self._k=key
    def __call__(self, o):
        return o[key]

class MultipleSelector:
    def __init__(self, keys):
        self._k=keys
    def __call__(self, o):
        r=[]
        a=r.append
        for key in self._k: a(o[key])
        return r
    

def getitems(o,names):
    r=[]
    for name in names:
        v=o[name]
        r.append(v)
    return r
        
