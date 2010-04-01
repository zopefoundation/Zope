##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Records

Records are used to provide compact storage for database query result rows.

They don't use instance dictionaries. Rather, they store they data in
a compact array internally. They use a record schema to map names to
positions within the array.

>>> class R(Record):
...     __record_schema__ = {'a': 0, 'b': 1, 'c': 2}

>>> r = R()
>>> r.__dict__
Traceback (most recent call last):
...
AttributeError: __dict__

>>> r.a
>>> r.a = 1
>>> r.a
1
>>> r.b
>>> r.c

Records can be used as mapping objects:

>>> "%(a)s %(b)s %(c)s" % r
'1 None None'

>>> r['a']
1

>>> r['b'] = 42

And like sequences:

>>> r[0]
1
>>> r[1]
42
>>> list(r)
[1, 42, None]

$Id: __init__.py,v 1.2 2003/11/28 16:46:36 jim Exp $
"""
from _Record import Record
