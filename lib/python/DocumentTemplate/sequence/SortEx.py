##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""
Advanced sort support by Oleg Broytmann <phd@@phd.pp.ru> 23 Apr 2001
eg Sort(sequence, (("akey", "nocase"), ("anotherkey", "cmp", "desc")))

$Id: SortEx.py,v 1.2 2001/05/23 14:42:08 andreas Exp $
"""

from string import lower
TupleType=type(())


def sort(sequence, sort=(), _=None, mapping=0):
    """
    - sequence is a sequence of objects to be sorted

    - sort is a sequence of tuples (key,func,direction)
      that define the sort order:

      - key is the name of an attribute to sort the objects by

      - func is the name of a comparison function. This parameter is
        optional

        allowed values:

        - "cmp" -- the standard comparison function (default)
 
        - "nocase" -- case-insensitive comparison
 
        - "strcoll" or "locale" -- locale-aware string comparison

        - "strcoll_nocase" or "locale_nocase" -- locale-aware case-insensitive
           string comparison
 
        - "xxx" -- a user-defined comparison function
 
      - direction -- defines the sort direction for the key (optional).
        (allowed values: "asc" (default) , "desc")
    """      



    need_sortfunc = 0
    if sort:
        for s in sort:
            if len(s) > 1: # extended sort if there is reference to...
                # ...comparison function or sort order, even if they are "cmp" and "asc"
                need_sortfunc = 1
                break

    sortfields = sort # multi sort = key1,key2 
    multsort = len(sortfields) > 1 # flag: is multiple sort

    if need_sortfunc:
        # prepare the list of functions and sort order multipliers
        sf_list = make_sortfunctions(sortfields, _)

        # clean the mess a bit
        if multsort: # More than one sort key.
            sortfields = map(lambda x: x[0], sf_list)
        else:
            sort = sf_list[0][0]

    elif sort:
        if multsort: # More than one sort key.
            sortfields = map(lambda x: x[0], sort)
        else:
            sort = sort[0][0]

    isort=not sort

    s=[]
    for client in sequence:
        k = None
        if type(client)==TupleType and len(client)==2:
            if isort: k=client[0]
            v=client[1]
        else:
            if isort: k=client
            v=client

        if sort:
             if multsort: # More than one sort key.
                 k = []
                 for sk in sortfields:
                     try:
                         if mapping: akey = v[sk]
                         else: akey = getattr(v, sk)
                     except AttributeError, KeyError: akey = None
                     if not basic_type(akey):
                         try: akey = akey()
                         except: pass
                     k.append(akey)
             else: # One sort key.
                 try:
                     if mapping: k = v[sort]
                     else: k = getattr(v, sort)
                 except AttributeError, KeyError: k = None
                 if not basic_type(type(k)):           
                     try: k = k()
                     except: pass

        s.append((k,client))

    if need_sortfunc:
        by = SortBy(multsort, sf_list)
        s.sort(by)
    else:
        s.sort()

    sequence=[]
    for k, client in s:
         sequence.append(client)
    return sequence


SortEx = sort

basic_type={type(''): 1, type(0): 1, type(0.0): 1, type(()): 1, type([]): 1,
            type(None) : 1 }.has_key

def nocase(str1, str2):
    return cmp(lower(str1), lower(str2))

import sys
if sys.modules.has_key("locale"): # only if locale is already imported
    from locale import strcoll

    def strcoll_nocase(str1, str2):
        return strcoll(lower(str1), lower(str2))


def make_sortfunctions(sortfields, _):
    """Accepts a list of sort fields; splits every field, finds comparison
    function. Returns a list of 3-tuples (field, cmp_function, asc_multplier)"""

    sf_list = []
    for field in sortfields:
        f = list(field)
        l = len(f)

        if l == 1:
            f.append("cmp")
            f.append("asc")
        elif l == 2:
            f.append("asc")
        elif l == 3:
            pass
        else:
            raise SyntaxError, "sort option must contains no more than 2 fields"

        f_name = f[1]

        # predefined function?
        if f_name == "cmp":
            func = cmp # builtin
        elif f_name == "nocase":
            func = nocase
        elif f_name in ("locale", "strcoll"):
            func = strcoll
        elif f_name in ("locale_nocase", "strcoll_nocase"):
            func = strcoll_nocase
        else: # no - look it up in the namespace
            func = _.getitem(f_name, 0)

        sort_order = lower(f[2])

        if sort_order == "asc":
            multiplier = +1
        elif sort_order == "desc":
            multiplier = -1
        else:
            raise SyntaxError, "sort oder must be either ASC or DESC"

        sf_list.append((f[0], func, multiplier))

    return sf_list


class SortBy:
    def __init__(self, multsort, sf_list):
        self.multsort = multsort
        self.sf_list = sf_list

    def __call__(self, o1, o2):
        multsort = self.multsort
        if multsort:
            o1 = o1[0] # if multsort - take the first element (key list)
            o2 = o2[0]

        sf_list = self.sf_list
        l = len(sf_list)

        # assert that o1 and o2 are tuples of apropriate length
        assert len(o1) == l + 1 - multsort, "%s, %d" % (o1, l + multsort)
        assert len(o2) == l + 1 - multsort, "%s, %d" % (o2, l + multsort)

        # now run through the list of functions in sf_list and
        # compare every object in o1 and o2
        for i in range(l):
            # if multsort - we already extracted the key list
            # if not multsort - i is 0, and the 0th element is the key
            c1, c2 = o1[i], o2[i]
            func, multiplier = sf_list[i][1:3]
            n = func(c1, c2)
            if n: return n*multiplier

        # all functions returned 0 - identical sequences
        return 0


