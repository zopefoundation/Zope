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
'''Nested namespace access

   The 'with' tag is used to introduce nested namespaces.

   The text enclosed in the with tag is rendered using information
   from the given variable or expression.

   For example, if the variable 'person' is bound to an object that
   has attributes 'name' and 'age', then a 'with' tag like the
   following can be used to access these attributes::

     <!--#with person-->
       <!--#var name-->,
       <!--#var age-->
     <!--#/with-->

   Eather a 'name' or an 'expr' attribute may be used to specify data.
   A 'mapping' attribute may be used to indicate that the given data
   should be treated as mapping object, rather than as an object with
   named attributes.

''' 

__rcs_id__='$Id: DT_With.py,v 1.9 1999/03/04 21:43:17 jim Exp $'
__version__='$Revision: 1.9 $'[11:-2]

from DT_Util import parse_params, name_param, InstanceDict, render_blocks, str
from DT_Util import TemplateDict
class With:
    blockContinuations=()
    name='with'
    mapping=None
    only=0
    
    def __init__(self, blocks):
        tname, args, section = blocks[0]
        args=parse_params(args, name='', expr='', mapping=1, only=1)
        name,expr=name_param(args,'with',1)
        if expr is None: expr=name
        else: expr=expr.eval
        self.__name__, self.expr = name, expr
        self.section=section.blocks
        if args.has_key('mapping') and args['mapping']: self.mapping=1
        if args.has_key('only') and args['only']: self.only=1

    def render(self, md):
        expr=self.expr
        if type(expr) is type(''): v=md[expr]
        else: v=expr(md)

        if not self.mapping:
            if type(v) is type(()) and len(v)==1: v=v[0]
            v=InstanceDict(v,md)

        if self.only:
            _md=md
            md=TemplateDict()
            if hasattr(_md, 'AUTHENTICATED_USER'):
                md.AUTHENTICATED_USER=_md.AUTHENTICATED_USER
            if hasattr(_md, 'validate'):
                md.validate=_md.validate

        md._push(v)
        try: return render_blocks(self.section, md)
        finally: md._pop(1)

    __call__=render
