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

__rcs_id__='$Id: DT_With.py,v 1.12 2001/04/27 20:27:39 shane Exp $'
__version__='$Revision: 1.12 $'[11:-2]

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
            if hasattr(_md, 'read_guard'):
                md.read_guard = _md.read_guard

        md._push(v)
        try: return render_blocks(self.section, md)
        finally: md._pop(1)

    __call__=render
