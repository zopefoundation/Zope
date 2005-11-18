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


import os,sys
from StructuredText.StructuredText import HTML


if len(sys.argv)>1:
    files = sys.argv[1:]
else:
    files = os.listdir('.')
    files = filter(lambda x: x.endswith('.stx'), files)


for f in files:

    data = open(f,'r').read()
    html = HTML(data)

    outfile = f.replace('.stx','.ref')
    open(outfile,'w').write(html)
