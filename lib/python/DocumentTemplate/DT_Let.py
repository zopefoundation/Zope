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

''' The Let tag was contributed to Zope by and is copyright, 1999
    Phillip J. Eby.  Permission has been granted to release the Let tag
    under the Zope Public License.
    

   Let name=value...

   The 'let' tag is used to bind variables to values within a block.

   The text enclosed in the let tag is rendered using information
   from the given variables or expressions.

   For example::

     <!--#let foofunc="foo()" my_bar=bar-->
       foo() = <!--#var foofunc-->,
       bar = <!--#var my_bar-->
     <!--#/let-->

   Notice that both 'name' and 'expr' style attributes may be used to
   specify data.  'name' style attributes (e.g. my_bar=bar) will be
   rendered as they are for var/with/in/etc.  Quoted attributes will
   be treated as Python expressions.

   Variables are processed in sequence, so later assignments can
   reference and/or overwrite the results of previous assignments,
   as desired.
''' 

from DT_Util import render_blocks, Eval, ParseError
from DT_Util import str # Probably needed due to hysterical pickles.
import re


class Let:
    blockContinuations=()
    name='let'
    
    def __init__(self, blocks):
        tname, args, section = blocks[0]
        self.__name__ = args
        self.section = section.blocks
        self.args = args = parse_let_params(args)

        for i in range(len(args)):
            name,expr = args[i]
            if expr[:1]=='"' and expr[-1:]=='"' and len(expr) > 1:
				# expr shorthand
                expr=expr[1:-1]
                try: args[i] = name, Eval(expr).eval
                except SyntaxError, v:
                    m,(huh,l,c,src) = v
                    raise ParseError, (
                        '<strong>Expression (Python) Syntax error</strong>:'
                        '\n<pre>\n%s\n</pre>\n' % v[0],
                        'let')
    def render(self, md):
        d={}; md._push(d)
        try:
            for name,expr in self.args:
                if type(expr) is type(''): d[name]=md[expr]
                else: d[name]=expr(md)
            return render_blocks(self.section, md)
        finally: md._pop(1)

    __call__ = render


def parse_let_params(text,
            result=None,
            tag='let',
            parmre=re.compile(
                r'([\0- ]*([^\0- =\"]+)=([^\0- =\"]+))'),
            qparmre=re.compile(
                r'([\0- ]*([^\0- =\"]+)="([^"]*)\")'),
            **parms):

    result=result or []

    mo = parmre.match(text)
    mo1= qparmre.match(text)

    if mo is not None:
        name=mo.group(2)
        value=mo.group(3)
        l=len(mo.group(1))
    elif mo1 is not None:
        name=mo1.group(2)
        value='"%s"' % mo1.group(3)
        l=len(mo1.group(1))
    else:
        if not text or not text.strip(): return result
        raise ParseError, ('invalid parameter: "%s"' % text, tag)

    result.append((name,value))

    text=text[l:].strip()
    if text: return apply(parse_let_params,(text,result,tag),parms)
    else: return result

