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
"""Load zope.conf for tests.

$Id: zopeconf.py 12915 2005-05-31 10:23:19Z philikon $
"""
import os
from os.path import join, abspath, dirname, split, exists

def process():
    """Read in zope.conf configuration file.

    This is a hack but there doesn't seem to be a better way.
    """
    _prefix = os.environ.get('INSTANCE_HOME')
    if not _prefix:
        try:
            __file__
        except NameError:
            # Test was called directly, so no __file__ global exists.
            _prefix = abspath(os.curdir)
        else:
            # Test was called by another test.
            _prefix = abspath(dirname(__file__))
        _prefix = join(_prefix, '..', '..', '..')

    _config = join(_prefix, 'etc', 'zope.conf')

    if exists(_config):
        from Zope import configure
        configure(_config)
