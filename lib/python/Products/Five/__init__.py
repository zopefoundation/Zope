##############################################################################
#
# Copyright (c) 2004 Five Contributors. All rights reserved.
#
# This software is distributed under the terms of the Zope Public
# License (ZPL) v2.1. See COPYING.txt for more information.
#
##############################################################################
"""Initialize the Five product

$Id: __init__.py 9796 2005-03-15 14:58:39Z efge $
"""
import Acquisition
from Globals import INSTANCE_HOME

import zcml

# public API provided by Five
# usage: from Products.Five import <something>
from browser import BrowserView, StandardMacros

def initialize(context):
    zcml.load_site()
