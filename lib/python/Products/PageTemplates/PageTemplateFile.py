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
"""Filesystem Page Template module

Zope object encapsulating a Page Template from the filesystem.
"""

__version__='$Revision: 1.3 $'[11:-2]

import os, AccessControl, Acquisition, sys
from Globals import package_home, DevelopmentMode
from zLOG import LOG, ERROR, INFO
from string import join, strip, rstrip, split, lower
from Shared.DC.Scripts.Script import Script, BindingsUI
from Shared.DC.Scripts.Signature import FuncCode
from AccessControl import getSecurityManager
from OFS.Traversable import Traversable
from PageTemplate import PageTemplate
from ZopePageTemplate import SecureModuleImporter
from ComputedAttribute import ComputedAttribute

class PageTemplateFile(Script, PageTemplate, Traversable):
    "Zope wrapper for filesystem Page Template using TAL, TALES, and METAL"
     
    meta_type = 'Page Template (File)'

    func_defaults = None
    func_code = FuncCode((), 0)
    _need__name__=1
    _v_last_read=0

    _default_bindings = {'name_subpath': 'traverse_subpath'}

    security = AccessControl.ClassSecurityInfo()
    security.declareObjectProtected('View')
    security.declareProtected('View', '__call__')
    security.declareProtected('View management screens',
      'read', 'document_src')

    def __init__(self, filename, _prefix=None, **kw):
        self.ZBindings_edit(self._default_bindings)
        if _prefix is None: _prefix=SOFTWARE_HOME
        elif type(_prefix) is not type(''):
            _prefix = package_home(_prefix)
        name = kw.get('__name__')
        if not name:
            name = os.path.split(filename)[-1]
        self.__name__ = name
        self.filename = filename = os.path.join(_prefix, filename + '.zpt')

    def pt_getContext(self):
        root = self.getPhysicalRoot()
        c = {'template': self,
             'here': self._getContext(),
             'container': self._getContainer(),
             'nothing': None,
             'options': {},
             'root': root,
             'request': getattr(root, 'REQUEST', None),
             'modules': SecureModuleImporter,
             }
        return c

    def _exec(self, bound_names, args, kw):
        """Call a Page Template"""
        self._cook_check()
        if not kw.has_key('args'):
            kw['args'] = args
        bound_names['options'] = kw

        try:
            self.REQUEST.RESPONSE.setHeader('content-type',
                                            self.content_type)
        except AttributeError: pass

        # Execute the template in a new security context.
        security=getSecurityManager()
        security.addContext(self)
        try:
            return self.pt_render(extra_context=bound_names)
        finally:
            security.removeContext(self)

    def _cook_check(self):
        if self._v_last_read and not DevelopmentMode:
            return
        __traceback_info__ = self.filename
        try:    mtime=os.stat(self.filename)[8]
        except: mtime=0
        if hasattr(self, '_v_program') and mtime == self._v_last_read:
            return
        self.pt_edit(open(self.filename), None)
        self._cook()
        if self._v_errors:
            LOG('PageTemplateFile', ERROR, 'Error in template',
                join(self._v_errors, '\n'))
            return
        self._v_last_read = mtime

    def document_src(self, REQUEST=None, RESPONSE=None):
        """Return expanded document source."""

        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', self.content_type)
        return self.read()

    def _get__roles__(self):
        imp = getattr(aq_parent(aq_inner(self)),
                      '%s__roles__' % self.__name__)
        if hasattr(imp, '__of__'):
            return imp.__of__(self)
        return imp

    __roles__ = ComputedAttribute(_get__roles__, 1)

    def __setstate__(self, state):
        raise StorageError, ("Instance of AntiPersistent class %s "
                             "cannot be stored." % self.__class__.__name__)

