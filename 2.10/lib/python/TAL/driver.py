#!/usr/bin/env python
##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""
Driver program to test METAL and TAL implementation.

Usage: driver.py [options] [file]
Options:
    -h / --help
        Print this message and exit.
    -H / --html
    -x / --xml
        Explicitly choose HTML or XML input.  The default is to automatically
        select based on the file extension.  These options are mutually
        exclusive.
    -l
        Lenient structure insertion.
    -m
        Macro expansion only
    -s
        Print intermediate opcodes only
    -t
        Leave TAL/METAL attributes in output
    -i
        Leave I18N substitution strings un-interpolated.

BBB 2005/05/01 -- to be removed after 12 months
"""
import zope.deprecation
zope.deprecation.moved('zope.tal.driver', '2.12')

if __name__ == "__main__":
    main()
