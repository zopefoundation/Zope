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

__rcs_id__='$Id$'
__version__='$Revision: 1.15 $'[11:-2]

from DocumentTemplate.DT_Util import parse_params, name_param
from DocumentTemplate.DT_Util import InstanceDict, render_blocks, str
from DocumentTemplate.DT_Util import TemplateDict

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
            if hasattr(_md, 'guarded_getattr'):
                md.guarded_getattr = _md.guarded_getattr
            if hasattr(_md, 'guarded_getitem'):
                md.guarded_getitem = _md.guarded_getitem

        md._push(v)
        try: return render_blocks(self.section, md)
        finally: md._pop(1)

    __call__=render
