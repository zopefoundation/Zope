from ZODB.BaseStorage import BaseStorage
from bsddb3 import db
import os, tempfile

class Base(BaseStorage):

    def __init__(self, name='', env=0, prefix="zodb_"):
        if type(env) is type(''):
            env=envFromString(env)
            if not name: name=env
        elif not name: name='bsddb3'

        BaseStorage.__init__(self, name)

        self._env=env
        self._prefix=prefix
        self._setupDbs()
        self._tmp=tempfile.TemporaryFile()
        self._init_oid()

    def _setupDB(self, name, flags=0):
        """Open an individual database and assign to an "_" attribute.
        """
        d=db.Db(self._env)
        if flags: d.set_flags(flags)
        d.open(self._prefix+name, db.DB_BTREE, db.DB_CREATE)
        setattr(self, '_'+name, d)
        return d

    def _setupDbs(self):
        """Set up the storages databases, typically using '_setupDB'.
        """

    def _init_oid(self):
        c=self._index.cursor()
        v=c.get(db.DB_LAST)
        if v: self._oid=v[0]
        else: self._oid='\0\0\0\0\0\0\0\0'

    _len=-1
    def __len__(self):
        l=self._len
        if l < 0:
            l=self._len=len(self._index)

        return l

    def new_oid(self, last=None):
        # increment the cached length:
        l=self._len
        if l >= 0: self._len=l+1
        return BaseStorage.new_oid(self, last)
        

    def getSize(self):
        # TBD
        return 0

    def _finish(self, tid, user, desc, ext):
        self._txn.commit()

    def _abort(self, tid, user, desc, ext):
        self._txn.abort()

    def _clear_temp(self):
        self._tmp.seek(0)

    def close(self):
        """Close the storage

        by closing the databases it uses and closing it's environment.
        """
        for name in self._dbnames():
            getattr(self, '_'+name).close()
            delattr(self, '_'+name)
        self._env.close()
        del self._env

    def _dbnames(self):
        """Return a list of the names of the databases used by the storage.
        """
        return ("index",)

def envFromString(name):
    if not os.path.exists(name): os.mkdir(name)
    e=db.DbEnv()
    e.open(name,
           db.DB_CREATE | db.DB_RECOVER
           | db.DB_INIT_MPOOL | db.DB_INIT_LOCK | db.DB_INIT_TXN
           )
    return e
