##############################################################################
#
# Copyright (c) 1998, Digital Creations, Fredericksburg, VA, USA.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#   o Redistributions of source code must retain the above copyright
#     notice, this list of conditions, and the disclaimer that follows.
# 
#   o Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions, and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
# 
#   o All advertising materials mentioning features or use of this
#     software must display the following acknowledgement:
# 
#       This product includes software developed by Digital Creations
#       and its contributors.
# 
#   o Neither the name of Digital Creations nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# 
# THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS AND CONTRIBUTORS *AS IS*
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL
# CREATIONS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
#
# 
# If you have questions regarding this software, contact:
#
#   Digital Creations, L.C.
#   910 Princess Ann Street
#   Fredericksburge, Virginia  22401
#
#   info@digicool.com
#
#   (540) 371-6909
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
__rcs_id__='$Id: DT_Raise.py,v 1.6 1998/09/02 21:06:04 jim Exp $'
__version__='$Revision: 1.6 $'[11:-2]

from DT_Util import parse_params, name_param, render_blocks

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
# Revision 1.6  1998/09/02 21:06:04  jim
# many changes for thread safety, bug fixes, and faster import
#
# Revision 1.5  1998/09/02 14:35:53  jim
# open source copyright
#
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
