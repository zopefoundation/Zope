##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
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
__rcs_id__='$Id: DT_If.py,v 1.15 1998/12/04 20:15:27 jim Exp $'
__version__='$Revision: 1.15 $'[11:-2]

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
