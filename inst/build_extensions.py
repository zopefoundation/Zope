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
"""Build the Zope Extension Modules

You must be in the directory containing this script.
"""

from do import *

print
print '-'*78
print 'Building extension modules'

# For Python 2, we want to skip some things
if sys.version[:1]=='2':
    do('cp ./lib/python/Setup20 ./lib/python/Setup')
else:
    do('cp ./lib/python/Setup15 ./lib/python/Setup')

make('lib','python')
make('lib','python','DocumentTemplate')
make('lib','python','ZODB')
make('lib','python','BTrees')
make('lib','python','AccessControl')
make('lib','python','SearchIndex')
make('lib','python','Shared','DC','xml','pyexpat')
make('lib','python','Products','PluginIndexes','TextIndex','Splitter','ZopeSplitter')
make('lib','python','Products','PluginIndexes','TextIndex','Splitter','ISO_8859_1_Splitter')
make('lib','python','Products','PluginIndexes','TextIndex','Splitter','UnicodeSplitter')

# Try to link/copy cPickle.so to BoboPOS to out-fox
# stock Python cPickle if using Python 1.5.2.
if sys.version[:1] != '2':
    cd('lib')
    files=filter(
        lambda f: string.lower(f[:8])=='cpickle.',
        os.listdir('python')
        )
    if files:
        cd('python'); cd('ZODB')
        for f in files:
            src=os.path.join('..',f)
            try: os.link(src,f)
            except: open(f,'wb').write(open(src,'rb').read())
        cd('..'); cd('..')
    cd('..')
