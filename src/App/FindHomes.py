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

import os


try:
    chome = os.environ['INSTANCE_HOME']
except KeyError:
    import Zope2
    base = os.path.dirname(Zope2.__file__)
    base = os.path.join(base, os.path.pardir, os.path.pardir)
    chome = os.path.realpath(base)
else:
    chome = os.path.realpath(chome)

INSTANCE_HOME = chome

try:
    CLIENT_HOME = os.environ['CLIENT_HOME']
except KeyError:
    CLIENT_HOME = os.path.join(INSTANCE_HOME, 'var')
