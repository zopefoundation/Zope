##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""DBTab exception classes.

$Id$
"""


class DBTabConfigurationError (Exception):
    """Error in dbtab configuration"""
    args = ()

class DBTabOverrideError (Exception):
    """DBTab has taken over some piece of functionality"""
    args = ()

