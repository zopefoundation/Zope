##############################################################################
# 
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
#############################################################################


import re
from TextOperators import operator_dict, Near
from types import ListType

_debug = 1


def parse(s):
    """Parse parentheses and quotes"""

    l = []
    tmp = s.lower()

    p = parens(tmp)

    while p is not None:

        # Look for quotes in the section of the string before
        # the parentheses, then parse the string inside the parens

        l = l + quotes(p[0])
        l.append(parse(p[1]))

        # continue looking through the rest of the string

        tmp = p[2]
        p = parens(tmp)

    return l + quotes(tmp)



def parse2(q, default_operator, operator_dict=operator_dict):
    """Find operators and operands"""

    isop = operator_dict.has_key
    i = 0

    while i < len(q):
        e = q[i]

        if isinstance(e, ListType):
            q[i] = parse2(e, default_operator)
            if i % 2:
                q.insert(i, default_operator)
                i+=1 

        elif i % 2:

            # This element should be an operator

            if isop(e):

                # Ensure that it is identical, not merely equal.
                q[i] = operator_dict[e]

            else:

                # Insert the default operator.
                q.insert(i, default_operator)
                i+=1 

        i+=1 

    return q


def parens(s, parens_re=re.compile('[()]').search):

    mo = parens_re(s)
    if mo is None: return
    
    open_index = mo.start(0) + 1
    paren_count = 0

    while mo is not None:
        index = mo.start(0)
    
        if s[index] == '(':
            paren_count = paren_count + 1

        else:
            paren_count = paren_count - 1
            if paren_count == 0:
                return (s[:open_index - 1], s[open_index:index],
                        s[index + 1:])
            if paren_count < 0:
                break
        mo = parens_re(s, index + 1)

    raise QueryError, "Mismatched parentheses"      


def quotes(s):

    if '"' not in s: return s.split()
    
    # split up quoted regions
    splitted = re.split('\s*\"\s*', s)

    if (len(splitted) % 2) == 0: raise QueryError, "Mismatched quotes"
    
    for i in range(1,len(splitted),2):

        # split the quoted region into words
        words = splitted[i] = splitted[i].split()
        
        # put the Proxmity operator in between quoted words
        j = len(words) - 1
        while j > 0:
            words.insert(j, Near)
            j = j - 1

    i = len(splitted) - 1
    while i >= 0:
        # split the non-quoted region into words
        splitted[i:i+1] = splitted[i].split()
        i = i - 2

    return filter(None, splitted)


def debug(*args):
    """ used by TextIndexNG for dev. purposes """

    import sys

    if _debug:

        for a in args:
            sys.stdout.write(str(a))

        sys.stdout.write('\n')
        sys.stdout.flush()
