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
__version__='$Revision: 1.6 $'[11:-2]

from DT_Util import parse_params, name_param, str
import  sys

class ReturnTag: 
    name='return'
    expr=None

    def __init__(self, args):
        args = parse_params(args, name='', expr='')
        name, expr = name_param(args,'var',1)
        self.__name__, self.expr = name, expr

    def render(self, md):
        name=self.__name__
        val=self.expr
        if val is None:
            val = md[name]
        else:
            val=val.eval(md)

        raise DTReturn(val)

    __call__=render

class DTReturn:
    def __init__(self, v):
        self.v=v
