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

$Id: __init__.py,v 1.7 2003/02/07 21:28:13 fdrake Exp $
"""
import os

# Set the INSTANCE_HOME to the Testing package directory
os.environ['INSTANCE_HOME'] = INSTANCE_HOME = os.path.dirname(__file__)

# Set the SOFTWARE_HOME to the directory containing the Testing package
# XXX This isn't a change, so why?
os.environ['SOFTWARE_HOME'] = SOFTWARE_HOME = os.path.dirname(INSTANCE_HOME)

# Note: we don't set os.environ['ZEO_CLIENT'] anymore because we
# really do need all the products to be initialized.  Some tests
# use the product registry.
