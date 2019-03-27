import os
from glob import glob

import ZODB
from ZODB.FileStorage import FileStorage


def makeDB():
    s = FileStorage('fs_tmp__%s' % os.getpid())
    return ZODB.DB(s)


def cleanDB():
    for fn in glob('fs_tmp__*'):
        os.remove(fn)
