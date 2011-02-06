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
__rcs_id__='$Id$'
__version__='$Revision: 1.19 $'[11:-2]

from DocumentTemplate.DT_Util import ParseError, parse_params, name_param, str

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

        self.simple_form=('i',)+tuple(sections)

class Unless:
    name='unless'
    blockContinuations=()

    def __init__(self, blocks):
        tname, args, section = blocks[0]
        args=parse_params(args, name='', expr='')
        name,expr=name_param(args,'unless',1)
        if expr is None: cond=name
        else: cond=expr.eval
        self.simple_form=('i',cond,None,section.blocks)

class Else(Unless):
    # The else tag is included for backward compatibility and is deprecated.
    name='else'
