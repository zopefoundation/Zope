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
"""Page Template module

HTML- and XML-based template objects using TAL, TALES, and METAL.
"""

__version__='$Revision: 1.13 $'[11:-2]

import os, sys, traceback, pprint
from TAL.TALParser import TALParser
from TAL.HTMLTALParser import HTMLTALParser
from TAL.TALGenerator import TALGenerator
from TAL.TALInterpreter import TALInterpreter
from Expressions import getEngine
from string import join, strip, rstrip, split, replace, lower, find
from cStringIO import StringIO
from ExtensionClass import Base

Z_DEBUG_MODE = os.environ.get('Z_DEBUG_MODE') == '1'

class MacroCollection(Base):
    def __of__(self, parent):
        return parent._v_macros

class PageTemplate:
    "Page Templates using TAL, TALES, and METAL"
     
    content_type = 'text/html'
    expand = 1
    _v_errors = ()
    _text = ''
    _error_start = '<!-- Page Template Diagnostics'

    macros = MacroCollection()

    def pt_edit(self, text, content_type):
        if content_type:
            self.content_type = str(content_type)
        if hasattr(text, 'read'):
            text = text.read()
        self.write(text)

    def pt_getContext(self):
        c = {'template': self,
             'options': {},
             'nothing': None,
             'request': None,
             'modules': ModuleImporter,
             }
        parent = getattr(self, 'aq_parent', None)
        if parent is not None:
            c['here'] = parent
            c['container'] = self.aq_inner.aq_parent
            while parent is not None:
                self = parent
                parent = getattr(self, 'aq_parent', None)
            c['root'] = self
        return c
    
    def pt_render(self, source=0, extra_context={}):
        """Render this Page Template"""
        if self._v_errors:
            raise RuntimeError, 'Page Template %s has errors.' % self.id
        output = StringIO()
        c = self.pt_getContext()
        c.update(extra_context)
        if Z_DEBUG_MODE:
            __traceback_info__ = pprint.pformat(c)

        TALInterpreter(self._v_program, self._v_macros,
                       getEngine().getContext(c),
                       output,
                       tal=not source, strictinsert=0)()
        return output.getvalue()

    def __call__(self, *args, **kwargs):
        if not kwargs.has_key('args'):
            kwargs['args'] = args
        return self.pt_render(extra_context={'options': kwargs})

    def pt_errors(self):
        return self._v_errors

    def write(self, text):
        assert type(text) is type('')
        if text[:len(self._error_start)] == self._error_start:
            errend = find(text, '-->')
            if errend >= 0:
                text = text[errend + 4:]
        if self._text != text:
            self._text = text
        self._cook()

    def read(self):
        if not self._v_errors:
            if not self.expand:
                return self._text
            try:
                return self.pt_render(source=1)
            except:
                return ('%s\n Macro expansion failed\n %s\n-->\n%s' %
                        (self._error_start, "%s: %s" % sys.exc_info()[:2],
                         self._text) )
                                  
        return ('%s\n %s\n-->\n%s' % (self._error_start,
                                      join(self._v_errors, '\n '),
                                      self._text))

    def _cook(self):
        """Compile the TAL and METAL statments.

        A Page Template must always be cooked, and cooking must not
        fail due to user input.
        """
        if self.html():
            gen = TALGenerator(getEngine(), xml=0)
            parser = HTMLTALParser(gen)
        else:
            gen = TALGenerator(getEngine())
            parser = TALParser(gen)

        self._v_errors = ()
        try:
            parser.parseString(self._text)
            self._v_program, self._v_macros = parser.getCode()
        except:
            self._v_errors = ["Compilation failed",
                              "%s: %s" % sys.exc_info()[:2]]

    def html(self):
        return self.content_type == 'text/html'

class _ModuleImporter:
    def __getitem__(self, module):
        mod = __import__(module)
        path = split(module, '.')
        for name in path[1:]:
            mod = getattr(mod, name)
        return mod

ModuleImporter = _ModuleImporter()
