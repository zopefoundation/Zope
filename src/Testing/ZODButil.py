from glob import glob
from ZODB.FileStorage import FileStorage

import os
import ZODB


def makeDB():
    s = FileStorage('fs_tmp__%s' % os.getpid())
    return ZODB.DB(s)


def cleanDB():
    for fn in glob('fs_tmp__*'):
        os.remove(fn)
