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

__doc__='''Conditional insertion

       Conditional insertion is performed using 'if' and 'else'
       commands.

       To include text when an object is true using the EPFS
       format, use::

          %(if name)[
               text 
          %(if name)]

       To include text when an object is true using the HTML
       format, use::

          <!--#if name-->
               text 
          <!--#/if name-->

       where 'name' is the name bound to the object.

       To include text when an object is false using the EPFS
       format, use::

          %(else name)[
               text 
          %(else name)]

       To include text when an object is false using the HTML
       format, use::

          <!--#else name-->
               text 
          <!--#/else name-->

       Finally to include text when an object is true and to
       include different text when the object is false using the
       EPFS format, use::

          %(if name)[
               true text 
          %(if name)]
          %(else name)[
               false text 
          %(else name)]

       and to include text when an object is true and to
       include different text when the object is false using the
       HTML format, use::

          <!--#if name-->
               true text 
          <!--#else name-->
               false text 
          <!--#/if name-->

       Notes:

       - if a variable is nor defined, it is considered to be false.

       - A variable if only evaluated once in an 'if' tag.  If the value
         is used inside the tag, including in enclosed tags, the
         variable is not reevaluated.

''' 
__rcs_id__='$Id: DT_If.py,v 1.12 1998/09/08 15:05:31 jim Exp $'
__version__='$Revision: 1.12 $'[11:-2]

from DT_Util import ParseError, parse_params, name_param, str

class If:
    blockContinuations='else','elif'
    name='if'
    elses=None
    expr=''

    def __init__(self, blocks):

	tname, args, section = blocks[0]
	args=parse_params(args, name='', expr='')
	name,expr=name_param(args,'if',1)
	self.__name__= name
	if expr is None: cond=name
	else: cond=expr.eval
	sections=[cond, section.blocks]

	if blocks[-1][0]=='else':
	    tname, args, section = blocks[-1]
	    del blocks[-1]
	    args=parse_params(args, name='')
	    if args:
		ename,expr=name_param(args,'else',1)
		if ename != name:
		    raise ParseError, ('name in else does not match if', 'in')
	    elses=section.blocks
	else: elses=None

	for tname, args, section in blocks[1:]:
	    if tname=='else':
		raise ParseError, (
		    'more than one else tag for a single if tag', 'in')
	    args=parse_params(args, name='', expr='')
	    name,expr=name_param(args,'elif',1)
	    if expr is None: cond=name
	    else: cond=expr.eval
	    sections.append(cond)
	    sections.append(section.blocks)

	if elses is not None: sections.append(elses)

	self.simple_form=tuple(sections)

class Unless:
    name='unless'
    blockContinuations=()

    def __init__(self, blocks):
	tname, args, section = blocks[0]
	args=parse_params(args, name='', expr='')
	name,expr=name_param(args,'unless',1)
	if expr is None: cond=name
	else: cond=expr.eval
	self.simple_form=(cond,None,section.blocks)

class Else(Unless):
    # The else tag is included for backward compatibility and is deprecated.
    name='else'


##########################################################################
#
# $Log: DT_If.py,v $
# Revision 1.12  1998/09/08 15:05:31  jim
# added str to DT_Util import to address pickling lamosities
#
# Revision 1.11  1998/09/02 21:06:03  jim
# many changes for thread safety, bug fixes, and faster import
#
# Revision 1.10  1998/09/02 14:35:52  jim
# open source copyright
#
# Revision 1.9  1998/04/02 17:37:35  jim
# Major redesign of block rendering. The code inside a block tag is
# compiled as a template but only the templates blocks are saved, and
# later rendered directly with render_blocks.
#
# Added with tag.
#
# Also, for the HTML syntax, we now allow spaces after # and after end
# or '/'.  So, the tags::
#
#   <!--#
#     with spam
#     -->
#
# and::
#
#   <!--#
#     end with
#     -->
#
# are valid.
#
# Revision 1.8  1998/01/14 18:23:42  jim
# Added expr to unless.
#
# Revision 1.7  1998/01/14 18:03:25  jim
# Added Unless tag as replacement for else tag.
#
# Revision 1.6  1997/12/31 20:32:11  jim
# If and else blocks now cache variables.
#
# Revision 1.5  1997/11/07 17:08:11  jim
# Changed so exception is raised if a sequence cannot be gotten during
# rendering.
#
# Revision 1.4  1997/09/25 18:56:38  jim
# fixed problem in reporting errors
#
# Revision 1.3  1997/09/22 14:42:49  jim
# added expr
#
# Revision 1.2  1997/09/08 15:35:40  jim
# Fixed bug that caused else blocks to render if blocks.
#
# Revision 1.1  1997/08/27 18:55:42  jim
# initial
#
