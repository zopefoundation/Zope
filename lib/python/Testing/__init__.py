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

$Id: __init__.py,v 1.8 2003/02/11 17:17:08 fdrake Exp $
"""
import os

import App.config

cfg = App.config.getConfiguration()

# Set the INSTANCE_HOME to the Testing package directory
cfg.instancehome = os.path.dirname(__file__)

# Make sure this change is propogated to all the legacy locations for
# this information.
App.config.setConfiguration(cfg)
