import ZODB, os
from ZODB.FileStorage import FileStorage
from ZODB.DemoStorage import DemoStorage

dfi = os.path.join(SOFTWARE_HOME, '..', '..', 'var', 'Data.fs.in')
dfi = os.path.abspath(dfi)
Storage = DemoStorage(base=FileStorage(dfi, read_only=1), quota=(1<<20))
