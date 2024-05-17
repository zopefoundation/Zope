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
"""Package wrapper for Page Templates

This wrapper allows the Page Template modules to be segregated in a
separate package.
"""
import os

from zope.contenttype import add_files


# Placeholder for Zope Product data
misc_ = {}

# import ZTUtils in order to make i importable through
# ZopeGuards.load_module() where an importable modules must be
# available in sys.modules
import ZTUtils  # NOQA


def initialize(context):
    # Import lazily, and defer initialization to the module
    from . import ZopePageTemplate
    ZopePageTemplate.initialize(context)

    # Add the custom MIME type information for Page Templates
    # to the Python mimetypes module so they are recognized correctly
    here = os.path.dirname(os.path.abspath(__file__))
    add_files([os.path.join(here, 'mime.types')])
