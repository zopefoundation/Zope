import ZODB
from ZODB.DemoStorage import DemoStorage

Storage = DemoStorage(quota=(1<<20))
