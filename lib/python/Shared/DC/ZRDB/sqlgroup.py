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

"""Inserting optional tests with 'sqlgroup'

    It is sometimes useful to make inputs to an SQL statement
    optinal.  Doing so can be difficult, because not only must the
    test be inserted conditionally, but SQL boolean operators may or
    may not need to be inserted depending on whether other, possibly
    optional, comparisons have been done.  The 'sqlgroup' tag
    automates the conditional insertion of boolean operators.

    The 'sqlgroup' tag is a block tag. It can
    have any number of 'and' and 'or' continuation tags.

    The 'sqlgroup' tag has an optional attribure, 'required' to
    specify groups that must include at least one test.  This is
    useful when you want to make sure that a query is qualified, but
    want to be very flexible about how it is qualified.

    Suppose we want to find people with a given first or nick name,
    city or minimum and maximum age.  Suppose we want all inputs to be
    optional, but want to require *some* input.  We can
    use DTML source like the following::

      <dtml-sqlgroup required>
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

$Id$
"""

############################################################################
#     Copyright
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################
__rcs_id__='$Id$'
__version__='$Revision: 1.10 $'[11:-2]

from DocumentTemplate.DT_Util import parse_params
str = __builtins__['str']
from string import strip, join
import sys

_TNAME_MAPPING = {'comma': ','}

class SQLGroup:
    blockContinuations = 'and', 'or', 'comma'
    name = 'sqlgroup'
    required = None
    where = None
    set = None
    noparens = None

    def __init__(self, blocks):

        self.blocks = blocks
        tname, args, section = blocks[0]
        self.__name__ = "%s %s" % (tname, args)
        args = parse_params(args, required=1, where=1, set=1, noparens=1)
        if args.has_key(''):
            args[args['']] = 1
        if args.has_key('required'):
            self.required = args['required']
        if args.has_key('where'):
            self.where = args['where']
        if args.has_key('set'):
            self.set = args['set']
        if args.has_key('noparens'):
            self.noparens = args['noparens']

    def render(self,md):

        r = []
        for tname, args, section in self.blocks:
            __traceback_info__ = tname
            s = strip(section(None, md))
            if s:
                if r:
                    r.append(_TNAME_MAPPING.get(tname, tname))
                if self.noparens:
                    r.append(s)
                else:
                    r.append("%s\n" % s)
        if r:
            if len(r) > 1:
                if self.noparens:
                    r = "%s\n" % join(r,' ')
                else:
                    r = "(%s)\n" % join(r,' ')
            else:
                r = r[0]
            if self.set:
                r = "set\n"+r
            if self.where:
                r = "where\n"+r
            return r

        if self.required:
            raise ValueError, 'Not enough input was provided!<p>'

        return ''

    __call__ = render
