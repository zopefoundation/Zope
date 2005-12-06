##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Demo StandardMacros

$Id: demomacros.py 12884 2005-05-30 13:10:41Z philikon $
"""
from Products.Five import StandardMacros as BaseMacros

class StandardMacros(BaseMacros):

    macro_pages = ('bird_macros', 'dog_macros')
    aliases = {'flying':'birdmacro',
               'walking':'dogmacro'}
