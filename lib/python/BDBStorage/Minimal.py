from base import Base
from bsddb3 import db
from struct import pack, unpack

class Minimal(Base):

    def _setupDbs(self):
        # Supports Base framework
        self._index=self._setupDB('current')
        self._setupDB('pickle')

    def load(self, oid, version):
        self._lock_acquire()
        try:
            s=self._index[oid]
            p=self._pickle[oid]
            return p, s # pickle, serial
        finally: self._lock_release()

    def store(self, oid, serial, data, version, transaction):
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        if version:
            raise POSException.Unsupported, "Versions aren't supported"

        self._lock_acquire()
        try:
            if self._index.has_key(oid):
                oserial=self._index[oid]
                if serial != oserial: raise POSException.ConflictError
                
            serial=self._serial
            self._tmp.write(oid+pack(">I", len(data)))
            self._tmp.write(data)
        finally: self._lock_release()

        return serial

    def _finish(self, tid, u, d, e):
        txn = self._env.txn_begin()
        try:
            serial_put=self._index.put
            pickle_put=self._pickle.put
            serial=self._serial
            tmp=self._tmp
            s=tmp.tell()
            tmp.seek(0)
            read=tmp.read
            l=0
            while l < s:
                oid, ldata = unpack(">8sI", read(12))
                data=read(ldata)
                l=l+ldata+12
                if ldata > s:
                    raise 'Temporary file corrupted'
                serial_put(oid, serial, txn)
                pickle_put(oid, data,   txn)

            tmp.seek(0)
            if s > 999999: tmp.truncate()
            
        except:
            txn.abort()
            raise
        else:
            txn.commit()

    def pack(self, t, referencesf):
        
        self._lock_acquire()
        try:
            # Build an index of *only* those objects reachable
            # from the root.
            index=self._pickle
            rootl=['\0\0\0\0\0\0\0\0']
            pop=rootl.pop
            pindex={}
            referenced=pindex.has_key
            while rootl:
                oid=pop()
                if referenced(oid): continue
    
                # Scan non-version pickle for references
                p=index[oid]
                pindex[oid]=1
                referencesf(p, rootl)

            # Now delete any unreferenced entries:
            for oid in index.keys():
                if not referenced(oid): del index[oid]
    
        finally: self._lock_release()









