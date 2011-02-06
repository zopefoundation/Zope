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
__version__='$Revision: 1.9 $'[11:-2]

from DocumentTemplate.DT_Util import parse_params, name_param

class ReturnTag:
    name='return'
    expr=None

    def __init__(self, args):
        args = parse_params(args, name='', expr='')
        name, expr = name_param(args, 'var', 1)
        self.__name__ = name
        self.expr = expr

    def render(self, md):
        if self.expr is None:
            val = md[self.__name__]
        else:
            val = self.expr.eval(md)

        raise DTReturn(val)

    __call__ = render

class DTReturn:
    def __init__(self, v):
        self.v = v
