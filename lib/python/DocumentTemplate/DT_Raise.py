
'''Raising exceptions

   Errors can be raised from DTML using the 'raise' tag.

   For example::

    <!--#if expr="condition_that_tests_input"-->
       <!--#raise type="Input Error"-->
           The value you entered is not valid
       <!--#/raise-->
    <!--#/if-->

''' 

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
__rcs_id__='$Id: DT_Raise.py,v 1.4 1998/05/14 15:07:17 jim Exp $'
__version__='$Revision: 1.4 $'[11:-2]

from DT_Util import *
import sys

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


##########################################################################
#
# $Log: DT_Raise.py,v $
# Revision 1.4  1998/05/14 15:07:17  jim
# Finished adding with and raise docs.
#
# Revision 1.3  1998/04/02 19:05:53  jim
# Updated rendering code.
#
# Revision 1.2  1998/03/04 18:50:39  jim
# *** empty log message ***
#
# Revision 1.1  1998/03/04 18:19:56  jim
# added comment and raise tags
#
