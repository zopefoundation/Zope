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
'''Raising exceptions

   Errors can be raised from DTML using the 'raise' tag.

   For example::

    <!--#if expr="condition_that_tests_input"-->
       <!--#raise type="Input Error"-->
           The value you entered is not valid
       <!--#/raise-->
    <!--#/if-->

'''
__rcs_id__='$Id: DT_Raise.py,v 1.13 2002/08/14 22:29:52 mj Exp $'
__version__='$Revision: 1.13 $'[11:-2]

from DT_Util import parse_params, name_param, render_blocks, str

class Raise:
    blockContinuations=()
    name='raise'
    expr=''

    def __init__(self, blocks):

        tname, args, section = blocks[0]
        self.section=section.blocks
        args=parse_params(args, type='', expr='')
        self.__name__, self.expr = name_param(args, 'raise', 1, attr='type')

    def render(self,md):
        expr=self.expr
        if expr is None:
            t=self.__name__
            if t[-5:]=='Error' and __builtins__.has_key(t):
                t=__builtins__[t]
        else:
            try: t=expr.eval(md)
            except: t='Invalid Error Type Expression'

        try: v=render_blocks(self.section,md)
        except: v='Invalid Error Value'

        raise t, v

    __call__=render
