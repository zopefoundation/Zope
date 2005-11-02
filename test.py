#!/usr/bin/env python
##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Zope 2 test script

see zope.testing testrunner.txt

$Id: test.py 33303 2005-07-13 22:28:33Z jim $
"""

import os.path, sys

shome = os.environ.get('SOFTWARE_HOME')
zhome = os.environ.get('ZOPE_HOME')
ihome = os.environ.get('INSTANCE_HOME')

if zhome:
    zhome = os.path.abspath(zhome)
    if shome:
        shome = os.path.abspath(shome)
    else:
        shome = os.path.join(zhome, 'lib/python')
elif shome:
    shome = os.path.abspath(shome)
    zhome = os.path.dirname(os.path.dirname(shome))
elif ihome:
    print >> sys.stderr, '''
    If INSTANCE_HOME is set, then at least one of SOFTWARE_HOME or ZOPE_HOME
    must be set
    '''
else:
    # No zope home, assume that it is the script directory
    zhome = os.path.abspath(os.path.dirname(sys.argv[0]))
    shome = os.path.join(zhome, 'lib/python')

sys.path.insert(0, shome)

defaults = '--tests-pattern ^tests$ -v'.split()
defaults += ['-m',
             '!^('
             'ZConfig'
             '|'
             'BTrees'
             '|'
             'persistentThreadedAsync'
             '|'
             'transaction'
             '|'
             'ZEO'
             '|'
             'ZODB'
             '|'
             'ZopeUndo'
             '|'
             'zdaemon'
             '|'
             'zope[.]testing'
             ')[.]']
if ihome:
    ihome = os.path.abspath(ihome)
    defaults += ['--path', os.path.join(ihome, 'lib', 'python')]
    products = os.path.join(ihome, 'Products')
    if os.path.exists(products):
        defaults += ['--package-path', products, 'Products']
else:
    defaults += ['--test-path', shome]

from zope.testing import testrunner

def load_config_file(option, opt, config_file, *ignored):
    config_file = os.path.abspath(config_file)
    print "Parsing %s" % config_file
    import Zope2
    Zope2.configure(config_file)

testrunner.setup.add_option(
    '--config-file', action="callback", type="string", dest='config_file',
    callback=load_config_file,
    help="""\
Initialize Zope with the given configuration file.
""")

sys.exit(testrunner.run(defaults))
