##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
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

      <dtml-sqlgroup>
        <dtml-sqlgroup>
          <dtml-sqltest name column=nick_name type=nb multiple optional>
        <dtml-or>
          <dtml-sqltest name column=first_name type=nb multiple optional>
        </dtml-sqlgroup>
      <dtml-and>
        <dtml-sqltest home_town type=nb optional>
      <dtml-and>
        <dtml-if minimum_age>
           age >= <dtml-sqlvar minimum_age type=int>
        </dtml-if>
      <dtml-and>
        <dtml-if maximum_age>
           age <= <dtml-sqlvar maximum_age type=int>
        </dtml-if>
      </dtml-sqlgroup>

    This example illustrates how groups can be nested to control
    boolean evaluation order.  It also illustrates that the grouping
    facility can also be used with other DTML tags like 'if' tags.

    The 'sqlgroup' tag checks to see if text to be inserted contains
    other than whitespace characters.  If it does, then it is inserted
    with the appropriate boolean operator, as indicated by use of an
    'and' or 'or' tag, otherwise, no text is inserted.

'''
__rcs_id__='$Id$'

############################################################################
#     Copyright
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################
__version__='$Revision: 1.5 $'[11:-2]

import sys
from DocumentTemplate.DT_Util import ParseError, parse_params, name_param
str=__builtins__['str']

from string import find, split, join, atoi, atof
from types import ListType, TupleType, StringType

class SQLTest:
    name='sqltest'
    optional=multiple=None

    def __init__(self, args):
        args = parse_params(args, name='', expr='', type=None, column=None,
                            multiple=1, optional=1, op=None)
        name,expr = name_param(args,'sqlvar',1)

        if expr is None:
            expr=name
        else: expr=expr.eval
        self.__name__, self.expr = name, expr

        self.args=args
        if not args.has_key('type'):
            raise ParseError, ('the type attribute is required', 'sqltest')

        self.type=t=args['type']
        if not valid_type(t):
            raise ParseError, ('invalid type, %s' % t, 'sqltest')

        if args.has_key('optional'): self.optional=args['optional']
        if args.has_key('multiple'): self.multiple=args['multiple']
        if args.has_key('column'):
            self.column=args['column']
        elif self.__name__ is None:
            err = ' the column attribute is required if an expression is used'
            raise ParseError, (err, 'sqltest')
        else:
            self.column=self.__name__

        # Deal with optional operator specification
        op = '='                        # Default
        if args.has_key('op'):
            op = args['op']
            # Try to get it from the chart, otherwise use the one provided
            op = comparison_operators.get(op, op)
        self.op = op

    def render(self, md):
        name=self.__name__

        t=self.type
        args=self.args
        try:
            expr=self.expr
            if type(expr) is type(''):
                v=md[expr]
            else:
                v=expr(md)
        except KeyError:
            if args.has_key('optional') and args['optional']:
                return ''
            raise ValueError, 'Missing input variable, <em>%s</em>' % name

        if type(v) in (ListType, TupleType):
            if len(v) > 1 and not self.multiple:
                raise ValueError, (
                    'multiple values are not allowed for <em>%s</em>'
                    % name)
        else: v=[v]

        vs=[]
        for v in v:
            if not v and type(v) is StringType and t != 'string': continue
            if t=='int':
                try:
                    if type(v) is StringType:
                        if v[-1:]=='L':
                            v=v[:-1]
                        atoi(v)
                    else: v=str(int(v))
                except ValueError:
                    raise ValueError, (
                        'Invalid integer value for <em>%s</em>' % name)
            elif t=='float':
                if not v and type(v) is StringType: continue
                try:
                    if type(v) is StringType: atof(v)
                    else: v=str(float(v))
                except ValueError:
                    raise ValueError, (
                        'Invalid floating-point value for <em>%s</em>' % name)

            else:
                if not isinstance(v, (str, unicode)):
                    v = str(v)
                v=md.getitem('sql_quote__',0)(v)
                #if find(v,"\'") >= 0: v=join(split(v,"\'"),"''")
                #v="'%s'" % v
            vs.append(v)

        if not vs and t=='nb':
            if args.has_key('optional') and args['optional']:
                return ''
            else:
                err = 'Invalid empty string value for <em>%s</em>' % name
                raise ValueError, err


        if not vs:
            if self.optional: return ''
            raise ValueError, (
                'No input was provided for <em>%s</em>' % name)

        if len(vs) > 1:
            vs=join(map(str,vs),', ')
            if self.op == '<>':
                ## Do the equivalent of 'not-equal' for a list,
                ## "a not in (b,c)"
                return "%s not in (%s)" % (self.column, vs)
            else:
                ## "a in (b,c)"
                return "%s in (%s)" % (self.column, vs)
        return "%s %s %s" % (self.column, self.op, vs[0])

    __call__=render

valid_type={'int':1, 'float':1, 'string':1, 'nb': 1}.has_key

comparison_operators = { 'eq': '=', 'ne': '<>',
                         'lt': '<', 'le': '<=', 'lte': '<=',
                         'gt': '>', 'ge': '>=', 'gte': '>=' }
