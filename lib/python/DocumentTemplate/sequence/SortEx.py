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
##############################################################################
"""
Advanced sort support by Oleg Broytmann <phd@@phd.pp.ru> 23 Apr 2001
eg Sort(sequence, (("akey", "nocase"), ("anotherkey", "cmp", "desc")))

$Id: SortEx.py,v 1.3 2001/11/28 15:50:55 matt Exp $
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


