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
'''Inserting values with the 'sqlvar' tag

    The 'sqlvar' tag is used to type-safely insert values into SQL
    text.  The 'sqlvar' tag is similar to the 'var' tag, except that
    it replaces text formatting parameters with SQL type information.

    The sqlvar tag has the following attributes:

      name -- The name of the variable to insert. As with other
              DTML tags, the 'name=' prefix may be, and usually is,
              ommitted.

      type -- The data type of the value to be inserted.  This
              attribute is required and may be one of 'string',
              'int', 'float', or 'nb'.  The 'nb' data type indicates a
              string that must have a length that is greater than 0.

      optional -- A flag indicating that a value is optional.  If a
                  value is optional and is not provided (or is blank
                  when a non-blank value is expected), then the string
                  'null' is inserted.

    For example, given the tag::

      <dtml-sqlvar x type=nb optional>

    if the value of 'x' is::
 
      Let\'s do it

    then the text inserted is:

      'Let''s do it'

    however, if x is ommitted or an empty string, then the value
    inserted is 'null'.
'''
__rcs_id__='$Id: sqlvar.py,v 1.10 2000/08/07 20:17:16 brian Exp $'

############################################################################
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################ 
__version__='$Revision: 1.10 $'[11:-2]

from DocumentTemplate.DT_Util import ParseError, parse_params, name_param
from string import find, split, join, atoi, atof
StringType=type('')

str=__builtins__['str']

class SQLVar: 
    name='sqlvar'

    def __init__(self, args):
        args = parse_params(args, name='', expr='', type=None, optional=1)

        name,expr=name_param(args,'sqlvar',1)
        if expr is None: expr=name
        else: expr=expr.eval
        self.__name__, self.expr = name, expr

        self.args=args
        if not args.has_key('type'):
            raise ParseError, ('the type attribute is required', 'dtvar')
        t=args['type']
        if not valid_type(t):
            raise ParseError, ('invalid type, %s' % t, 'dtvar')

    def render(self, md):
        name=self.__name__
        args=self.args
        t=args['type']
        try:
            expr=self.expr
            if type(expr) is type(''): v=md[expr]
            else: v=expr(md)
        except:
            if args.has_key('optional') and args['optional']:
                return 'null'
            if type(expr) is not type(''):
                raise
            raise 'Missing Input', 'Missing input variable, <em>%s</em>' % name

        if t=='int':
            try:
                if type(v) is StringType: atoi(v)
                else: v=str(int(v))
            except:
                if not v and args.has_key('optional') and args['optional']:
                    return 'null'
                raise ValueError, (
                    'Invalid integer value for <em>%s</em>' % name)
        elif t=='float':
            try:
                if type(v) is StringType: atof(v)
                else: v=str(float(v))
            except:
                if not v and args.has_key('optional') and args['optional']:
                    return 'null'
                raise ValueError, (
                    'Invalid floating-point value for <em>%s</em>' % name)
        else:
            v=str(v)
            if not v and t=='nb':
                if args.has_key('optional') and args['optional']:
                    return 'null'
                else:
                    raise ValueError, (
                        'Invalid empty string value for <em>%s</em>' % name)
            
            v=md.getitem('sql_quote__',0)(v)
            #if find(v,"\'") >= 0: v=join(split(v,"\'"),"''")
            #v="'%s'" % v

        return v

    __call__=render

valid_type={'int':1, 'float':1, 'string':1, 'nb': 1}.has_key
