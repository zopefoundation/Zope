
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

__rcs_id__='$Id: DT_With.py,v 1.1 1998/04/02 17:37:38 jim Exp $'

############################################################################
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
#  
#
# If you have questions regarding this software,
# contact:
#
#   Jim Fulton, jim@digicool.com
#
#   (540) 371-6909
#
############################################################################ 
__version__='$Revision: 1.1 $'[11:-2]

from DT_Util import *

class With:
    blockContinuations=()
    name='with'
    mapping=None
    
    def __init__(self, blocks):
	tname, args, section = blocks[0]
	args=parse_params(args, name='', expr='', mapping=1)
	name,expr=name_param(args,'with',1)
	if expr is None: expr=name
	else: expr=expr.eval
	self.__name__, self.expr = name, expr
	self.section=section.blocks
	if args.has_key('mapping') and args['mapping']: self.mapping=1

    def render(self, md):
	expr=self.expr
	if type(expr) is type(''): v=md[expr]
	else: v=expr(md)
	
	if self.mapping: md._push(v)
	else:
	    if type(v) is type(()) and len(v)==1: v=v[0]
	    md._push(InstanceDict(v,md))

	try: return render_blocks(self.section, md)
	finally: md._pop(1)

    __call__=render
