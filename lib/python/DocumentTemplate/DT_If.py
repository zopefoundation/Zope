##############################################################################
#
# Copyright (c) 1996-1998, Digital Creations, Fredericksburg, VA, USA.
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
__rcs_id__='$Id: DT_If.py,v 1.14 1998/09/14 22:03:31 jim Exp $'
__version__='$Revision: 1.14 $'[11:-2]

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
