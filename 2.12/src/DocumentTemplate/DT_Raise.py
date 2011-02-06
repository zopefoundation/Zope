##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
'''Raising exceptions

   Errors can be raised from DTML using the 'raise' tag.

   For example::

    <!--#if expr="condition_that_tests_input"-->
       <!--#raise type="Input Error"-->
           The value you entered is not valid
       <!--#/raise-->
    <!--#/if-->

'''
__rcs_id__='$Id$'
__version__='$Revision: 1.13 $'[11:-2]

from zExceptions import upgradeException
from zExceptions import convertExceptionType
from DocumentTemplate.DT_Util import name_param
from DocumentTemplate.DT_Util import parse_params
from DocumentTemplate.DT_Util import render_blocks

class InvalidErrorTypeExpression(Exception):
    pass

class Raise:
    blockContinuations=()
    name='raise'
    expr=''

    def __init__(self, blocks):

        tname, args, section = blocks[0]
        self.section = section.blocks
        args = parse_params(args, type='', expr='')
        self.__name__, self.expr = name_param(args, 'raise', 1, attr='type')

    def render(self,md):
        expr = self.expr
        if expr is None:
            t = convertExceptionType(self.__name__)
            if t is None:
                t = RuntimeError
        else:
            try:
                t = expr.eval(md)
            except:
                t = convertExceptionType(self.__name__)
                if t is None:
                    t = InvalidErrorTypeExpression

        try:
            v = render_blocks(self.section, md)
        except:
            v = 'Invalid Error Value'
        
        # String Exceptions are deprecated on Python 2.5 and
        # plain won't work at all on Python 2.6. So try to upgrade it
        # to a real exception.
        t, v = upgradeException(t, v)
        raise t, v

    __call__ = render
