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

import os
from do import *

def main(home, user='', group=''):
    data_dir=os.path.join(home,'var')
    ch(data_dir, user, group, 0711)
    db_path=os.path.join(data_dir, 'Data.fs')
    dd_path=os.path.join(data_dir, 'Data.fs.in')
    if not os.path.exists(db_path) and os.path.exists(dd_path):
        print '-'*78
        print 'setting dir permissions'
        def dir_chmod(mode, dir, files, user=user, group=group):
            ch(dir, user=user, group=group, mode=mode, quiet=1)
        os.path.walk(home, dir_chmod, 0775)
        print '-'*78
        print 'creating default database'
        open(db_path,'wb').write(open(dd_path,'rb').read())
        ch(db_path, user, group)




