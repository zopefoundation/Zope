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
Set up testing environment

$Id: __init__.py,v 1.4 2001/11/28 15:51:17 matt Exp $
"""
import os

def pdir(path):
    return os.path.split(path)[0]

# Set the INSTANCE_HOME to the Testing package directory
os.environ['INSTANCE_HOME'] = INSTANCE_HOME = pdir(__file__)

# Set the SOFTWARE_HOME to the directory containing the Testing package
os.environ['SOFTWARE_HOME'] = SOFTWARE_HOME = pdir(INSTANCE_HOME)

# Prevent useless initialization by pretending to be a ZEO client
os.environ['ZEO_CLIENT'] = '1'


