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
"""
The Zope run script.

Usage: runzope [-C URL][-h] [options]

Options:
-C/--configure URL -- configuration file or URL
-X -- overwrite config file settings, e.g. -X "debug-mode=on"
-h/--help -- print this usage message and exit
"""

import os

import zdaemon.zdoptions


class ZopeOptions(zdaemon.zdoptions.ZDOptions):

    # Provide help message, without indentation.
    __doc__ = __doc__

    schemadir = os.path.dirname(os.path.abspath(__file__))
    schemafile = "zopeschema.xml"
