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

"""Generic Python Expression Handler
"""

__version__='$Revision: 1.5 $'[11:-2]

from TALES import CompilerError
from string import strip, split, join, replace, lstrip
from sys import exc_info

class getSecurityManager:
    '''Null security manager'''
    def validate(self, *args, **kwargs):
        return 1
    addContext = removeContext = validateValue = validate

class PythonExpr:
    def __init__(self, name, expr, engine):
        self.expr = expr = replace(strip(expr), '\n', ' ')
        try:
            d = {}
            exec 'def f():\n return %s\n' % strip(expr) in d
            self._f = d['f']
        except:
            raise CompilerError, ('Python expression error:\n'
                                  '%s: %s') % exc_info()[:2]
        self._get_used_names()

    def _get_used_names(self):
        self._f_varnames = vnames = []
        for vname in self._f.func_code.co_names:
            if vname[0] not in '$_':
                vnames.append(vname)

    def _bind_used_names(self, econtext):
        # Bind template variables
        names = {}
        vars = econtext.vars
        getType = econtext._engine.getTypes().get
        for vname in self._f_varnames:
            has, val = vars.has_get(vname)
            if not has:
                has = val = getType(vname)
                if has:
                    val = ExprTypeProxy(vname, val, econtext)
            if has:
                names[vname] = val
        return names

    def __call__(self, econtext):
        __traceback_info__ = self.expr
        f = self._f
        f.func_globals.update(self._bind_used_names(econtext))        
        return f()

    def __str__(self):
        return 'Python expression "%s"' % self.expr
    def __repr__(self):
        return '<PythonExpr %s>' % self.expr

class ExprTypeProxy:
    '''Class that proxies access to an expression type handler'''
    def __init__(self, name, handler, econtext):
        self._name = name
        self._handler = handler
        self._econtext = econtext
    def __call__(self, text):
        return self._handler(self._name, text,
                             self._econtext._engine)(self._econtext)

