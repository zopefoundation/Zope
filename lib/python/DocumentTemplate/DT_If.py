
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

       Note that if a variable is nor defined, it is considered to be false.
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
__rcs_id__='$Id: DT_If.py,v 1.1 1997/08/27 18:55:42 jim Exp $'
__version__='$Revision: 1.1 $'[11:-2]

from DT_Util import *

class If:
    blockContinuations='else','elif'
    name='if'
    elses=None

    def __init__(self, blocks):
	tname, args, section = blocks[0]
	args=parse_params(args, name='')
	name=name_param(args)
	self.__name__ = name
	self.sections=[(name, section)]
	if blocks[-1][0]=='else':
	    tname, args, section = blocks[0]
	    blocks=blocks[:-1]
	    args=parse_params(args, name='')
	    if args:
		ename=name_param(args)
		if ename != name:
		    raise ParseError, 'name in else does not match if'
	    self.elses=section

	for tname, args, section in blocks[1:]:
	    if tname=='else':
		raise ParseError, 'more than one else tag for a single if tag'
	    name=name_param(args)
	    self.sections.append((name, section))

    def render(self,md):
	for name, section in self.sections:
	    try: v=md[name]
	    except: v=None
	    if v: return section(None,md)

	if self.elses: return self.elses(None, md)
	return ''

    __call__=render

class Else:
    name='else'
    blockContinuations=()

    def __init__(self, blocks):
	tname, args, section = blocks[0]
	args=parse_params(args, name='')
	name=name_param(args)
	self.__name__ = name
	self.section=section

    def render(self,md):
	try: v=md[self.__name__]
	except: v=None
	if not v: return self.section(None,md)
	return ''

    __call__=render

##########################################################################
#
# $Log: DT_If.py,v $
# Revision 1.1  1997/08/27 18:55:42  jim
# initial
#
