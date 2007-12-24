##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################


""" Generate svn:external files (with help of the KGS)
    Written by Andreas Jung, 2007
"""

import sys
import os
import urllib2
from ConfigParser import ConfigParser, NoOptionError

error = sys.stderr

# retrieve externals used in Zope 2
os.system('svn propget svn:externals lib/python >lib_python.txt')
os.system('svn propget svn:externals lib/python/zope >lib_python_zope.txt')
os.system('svn propget svn:externals lib/python/zope/app >lib_python_zope_app.txt')

# download current KGS index
kgs_url = 'http://download.zope.org/zope3.4/versions.cfg'
open('kgs.ini', 'w').write(urllib2.urlopen(kgs_url).read())
CP = ConfigParser()
CP.read('kgs.ini')

for name, prefix in (('lib_python', None), 
                     ('lib_python_zope', 'zope'), 
                     ('lib_python_zope_app', 'zope.app')):

    outname = name + '.ext'
    print >>error, 'Generating externals file %s' % outname

    fp = open(outname, 'w')
    for line in open(name + '.txt'):
        line = line.strip()
        if not line: continue
        module, url = line.split(' ', 1)
        module = module.strip()
        url = url.strip()

        # generate full module name as it appear in the KGS idnex
        full_mod_name = module
        if prefix:
            full_mod_name = '%s.%s' % (prefix, module)

        try:
            tag = CP.get('versions', full_mod_name)
            n = '/'.join(full_mod_name.split('.'))
            url = 'svn://svn.zope.org/repos/main/%s/tags/%s/src/%s' % (full_mod_name, tag, n)
            ok = True
        except NoOptionError:
            ok = False
            print >>error, 'WARN: KGS incomplete - %s not found' % full_mod_name

        if not ok:
            print >>fp, '# warning: KGS incomplete, using old URL for %s' % module
        print >>fp, '%-20s %s' % (module, url)                
    fp.close()
