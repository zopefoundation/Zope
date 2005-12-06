#!/usr/bin/env python2.4
##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Test script for running unit tests in a distribution root.

The functional tests can't be run since we don't have enough of the
package configuration in a usable state.  The functional tests can be
run from an installation.

$Id$
"""
import sys, os
from distutils.util import get_platform

PLAT_SPEC = "%s-%s" % (get_platform(), sys.version[0:3])

here = os.path.dirname(os.path.realpath(__file__))
lib = os.path.join(here, "build", "lib." + PLAT_SPEC)
sys.path.append(lib)

import zope.app.testing.test

if __name__ == '__main__':
    args = sys.argv[:1] + ["-ul", lib] + sys.argv[1:]
    zope.app.testing.test.process_args(args)
