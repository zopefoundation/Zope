##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

import DocumentTemplate, Common, Persistence, MethodObject, Globals, os

class HTML(DocumentTemplate.HTML,Persistence.Persistent,):
    "Persistent HTML Document Templates"

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
        elif type(_prefix) is not type(''):
            _prefix=Common.package_home(_prefix)
        args=(self, os.path.join(_prefix, name + '.dtml'))
        if not kw.has_key('__name__'):
            kw['__name__']=os.path.split(name)[-1]
        apply(HTMLFile.inheritedAttribute('__init__'),args,kw)

    def _cook_check(self):
        if Globals.DevelopmentMode:
            __traceback_info__=self.raw
            try:    mtime=os.stat(self.raw)[8]
            except: mtime=0
            if mtime != self._v_last_read:
                self.cook()
                self._v_last_read=mtime
        elif not hasattr(self,'_v_cooked'):
            try: changed=self.__changed__()
            except: changed=1
            self.cook()
            if not changed: self.__changed__(0)

    def __call__(self, *args, **kw):
        self._cook_check()
        return apply(HTMLFile.inheritedAttribute('__call__'),
                     (self,)+args[1:],kw)

defaultBindings = {'name_context': 'context',
                   'name_container': 'container',
                   'name_m_self': 'self',
                   'name_ns': '_',
                   'name_subpath': 'traverse_subpath'}

from Shared.DC.Scripts.Bindings import Bindings
from Acquisition import Explicit
from DocumentTemplate.DT_String import _marker, DTReturn, render_blocks
from DocumentTemplate.DT_Util import TemplateDict, InstanceDict

class DTMLFile(Bindings, Explicit, HTMLFile):
    "HTMLFile with bindings and support for __render_with_namespace__"
    
    class func_code: pass
    func_code=func_code()
    func_code.co_varnames=()
    func_code.co_argcount=0

    _Bindings_ns_class = TemplateDict

    def __init__(self, name, _prefix=None, **kw):
        self.ZBindings_edit(defaultBindings)
        apply(DTMLFile.inheritedAttribute('__init__'),
              (self, name, _prefix), kw)
    
    def _exec(self, bound_data, args, kw):
        # Cook if we haven't already
        self._cook_check()
        
        # Get our namespace
        name_ns = self.getBindingAssignments().getAssignedName('name_ns')
        ns = bound_data[name_ns]
        push = ns._push
        ns.validate = None

        # Check for excessive recursion
        level = ns.level
        if level > 200: raise SystemError, (
            'infinite recursion in document template')
        ns.level = level + 1

        req = None
        kw_bind = kw
        if level == 0:
            # If this is the starting namespace, get the REQUEST.
            try:
                req = self.aq_acquire('REQUEST')
            except: pass
        else:
            # Get last set of bindings.  Copy the request reference
            # forward, and include older keyword arguments in the
            # current 'keyword_args' binding.
            try:
                last_bound = ns[('current bindings',)]
                req = last_bound.get('REQUEST', None)
                old_kw = last_bound['keyword_args']
                if old_kw:
                    kw_bind = old_kw.copy()
                    kw_bind.update(kw)
            except: pass
        # Add 'REQUEST' and 'keyword_args' bound names.
        if req:
            bound_data['REQUEST'] = req
        bound_data['keyword_args'] = kw_bind

        # Push globals, initialized variables, REQUEST (if any),
        # and keyword arguments onto the namespace stack, followed
        # by the the container and the bound names.

        for nsitem in (self.globals, self._vars, req, kw):
            if nsitem:
                push(nsitem)

        # This causes dtml files to bypass their context unless they
        # explicitly use it through the 'context' name binding.
        push(InstanceDict(self._getContainer(), ns))
            
        push(bound_data)
        push({('current bindings',): bound_data})

        try:
            value = self.ZDocumentTemplate_beforeRender(ns, _marker)
            if value is _marker:
                try: result = render_blocks(self._v_blocks, ns)
                except DTReturn, v: result = v.v
                self.ZDocumentTemplate_afterRender(ns, result)
                return result
            else:
                return value
        finally:
            # Clear the namespace
            while len(ns): ns._pop()





