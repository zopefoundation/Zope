##############################################################################
#
# Zope Public License (ZPL) Version 0.9.5
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
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
# 3. Any use, including use of the Zope software to operate a website,
#    must either comply with the terms described below under
#    "Attribution" or alternatively secure a separate license from
#    Digital Creations.  Digital Creations will not unreasonably
#    deny such a separate license in the event that the request
#    explains in detail a valid reason for withholding attribution.
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
# Attribution
# 
#   Individuals or organizations using this software as a web site must
#   provide attribution by placing the accompanying "button" and a link
#   to the accompanying "credits page" on the website's main entry
#   point.  In cases where this placement of attribution is not
#   feasible, a separate arrangment must be concluded with Digital
#   Creations.  Those using the software for purposes other than web
#   sites must provide a corresponding attribution in locations that
#   include a copyright using a manner best suited to the application
#   environment.  Where attribution is not possible, or is considered
#   to be onerous for some other reason, a request should be made to
#   Digital Creations to waive this requirement in writing.  As stated
#   above, for valid requests, Digital Creations will not unreasonably
#   deny such requests.
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
'''Inserting optional tests with 'sqlgroup'
  
    It is sometimes useful to make inputs to an SQL statement
    optinal.  Doing so can be difficult, because not only must the
    test be inserted conditionally, but SQL boolean operators may or
    may not need to be inserted depending on whether other, possibly
    optional, comparisons have been done.  The 'sqlgroup' tag
    automates the conditional insertion of boolean operators.  

    The 'sqlgroup' tag is a block tag that has no attributes. It can
    have any number of 'and' and 'or' continuation tags.

    Suppose we want to find all people with a given first or nick name
    and optionally constrain the search by city and minimum and
    maximum age.  Suppose we want all inputs to be optional.  We can
    use DTML source like the following::

      <!--#sqlgroup-->
        <!--#sqlgroup-->
          <!--#sqltest name column=nick_name type=nb multiple optional-->
        <!--#or-->
          <!--#sqltest name column=first_name type=nb multiple optional-->
        <!--#/sqlgroup-->
      <!--#and-->
        <!--#sqltest home_town type=nb optional-->
      <!--#and-->
        <!--#if minimum_age-->
           age >= <!--#sqlvar minimum_age type=int-->
        <!--#/if-->
      <!--#and-->
        <!--#if maximum_age-->
           age <= <!--#sqlvar maximum_age type=int-->
        <!--#/if-->
      <!--#/sqlgroup-->

    This example illustrates how groups can be nested to control
    boolean evaluation order.  It also illustrates that the grouping
    facility can also be used with other DTML tags like 'if' tags.

    The 'sqlgroup' tag checks to see if text to be inserted contains
    other than whitespace characters.  If it does, then it is inserted
    with the appropriate boolean operator, as indicated by use of an
    'and' or 'or' tag, otherwise, no text is inserted.

'''
__rcs_id__='$Id: sqltest.py,v 1.8 1998/12/16 15:25:49 jim Exp $'

############################################################################
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################ 
__version__='$Revision: 1.8 $'[11:-2]

import sys
from DocumentTemplate.DT_Util import ParseError, parse_params, name_param
str=__builtins__['str']

from string import find, split, join, atoi, atof
from types import ListType, TupleType, StringType

class SQLTest: 
    name='sqltest'
    optional=multiple=None

    def __init__(self, args):
        args = parse_params(args, name='', type=None, column=None,
                            multiple=1, optional=1)
        self.__name__ = name_param(args,'sqlvar')
        has_key=args.has_key
        if not has_key('type'):
            raise ParseError, ('the type attribute is required', 'dtvar')
        self.type=t=args['type']
        if not valid_type(t):
            raise ParseError, ('invalid type, %s' % t, 'dtvar')
        if has_key('optional'): self.optional=args['optional']
        if has_key('multiple'): self.multiple=args['multiple']
        if has_key('column'): self.column=args['column']
        else: self.column=self.__name__

    def render(self, md):
        name=self.__name__
        t=self.type
        try: v = md[name]
        except KeyError, key:
            if key==name and self.optional: return ''
            raise KeyError, key, sys.exc_traceback
            
        
        if type(v) in (ListType, TupleType):
            if len(v) > 1 and not self.multiple:
                raise 'Multiple Values', (
                    'multiple values are not allowed for <em>%s</em>'
                    % name)
        else: v=[v]
        
        vs=[]
        for v in v:
            if not v and type(v) is StringType and t != 'string': continue
            if t=='int':
                try:
                    if type(v) is StringType: atoi(v)
                    else: v=str(int(v))
                except:
                    raise ValueError, (
                        'Invalid integer value for <em>%s</em>' % name)
            elif t=='float':
                if not v and type(v) is StringType: continue
                try:
                    if type(v) is StringType: atof(v)
                    else: v=str(float(v))
                except:
                    raise ValueError, (
                        'Invalid floating-point value for <em>%s</em>' % name)
            else:
                v=str(v)
                v=md.getitem('sql_quote__',0)(v)
                #if find(v,"\'") >= 0: v=join(split(v,"\'"),"''")
                #v="'%s'" % v
    
            vs.append(v)

        if not vs:
            if self.optional: return ''
            raise 'Missing Input', (
                'No input was provided for <em>%s</em>' % name)

        if len(vs) > 1:
            vs=join(map(str,vs),', ')
            return "%s in (%s)" % (self.column,vs)
        return "%s=%s" % (self.column,vs[0])

    __call__=render

valid_type={'int':1, 'float':1, 'string':1, 'nb': 1}.has_key
