from base import Base
from bsddb3 import db
from struct import pack, unpack
from ZODB.referencesf import referencesf

class Packless(Base):

    def _setupDbs(self):
        # Supports Base framework
        self._index=self._setupDB('current')
        self._setupDB('referenceCount')
        self._setupDB('oreferences', flags=db.DB_DUP)
        self._setupDB('opickle')

    def _dbnames(self):
        return 'current', 'referenceCount', 'oreferences', 'opickle'

    def load(self, oid, version):
        self._lock_acquire()
        try:
            s=self._index[oid]
            p=self._opickle[oid]
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
            zeros={}
            referenceCount=self._referenceCount
            referenceCount_get=referenceCount.get
            referenceCount_put=referenceCount.put
            oreferences=self._oreferences
            oreferences_put=oreferences.put
            serial_put=self._index.put
            opickle_put=self._opickle.put
            serial=self._serial
            tmp=self._tmp
            s=tmp.tell()
            tmp.seek(0)
            read=tmp.read
            l=0
            while l < s:
                oid, ldata = unpack(">8sI", read(12))
                data=read(ldata)

                # get references
                referencesl=[]
                referencesf(data, referencesl)
                references={}
                for roid in referencesl: references[roid]=1
                referenced=references.has_key

                # Create refcnt
                if not referenceCount_get(oid, txn):
                    referenceCount_put(oid, '\0\0\0\0', txn)
                    zeros[oid]=1
                
                # update stored references
                c=oreferences.cursor(txn)
                try:
                    try: roid = c.set(oid)
                    except:
                        pass
                    else:
                        while roid:
                            roid=roid[1]
                            if referenced(roid):
                                # still referenced, so no need to update
                                del references[roid]
                            else:
                                # Delete the stored ref, since we no longer
                                # have it
                                c.delete()
                                # decrement refcnt:
                                rc=unpack(">i",
                                          referenceCount_get(roid, txn))[0]
                                rc=rc-1
                                if rc < 0:
                                    raise "Bad reference count, %s" % (rc+1)
                                referenceCount_put(roid, pack(">i", rc), txn)
                                if rc==0: zeros[roid]=1
                            roid=c.get(db.DB_NEXT_DUP)

                finally: c.close()

                # Now add any references that weren't already stored:
                for roid in references.keys():
                    oreferences_put(oid, roid, txn)

                    # Create/update refcnt
                    rc=referenceCount_get(roid, txn)
                    if rc:
                        rc=unpack(">i", rc)[0]
                        if rc=='\0\0\0\0': del zeros[roid]
                        referenceCount_put(roid, pack(">i", rc+1), txn)
                    else:
                        referenceCount_put(roid, '\0\0\0\1', txn)
                
                l=l+ldata+12
                if ldata > s:
                    raise 'Temporary file corrupted'
                serial_put(oid, serial, txn)
                opickle_put(oid, data, txn)

            if zeros:
                for oid in zeros.keys():
                    if oid == '\0\0\0\0\0\0\0\0': continue
                    self._takeOutGarbage(oid, txn)
                    
            tmp.seek(0)
            if s > 999999: tmp.truncate()
            
        except:
            txn.abort()
            raise
        else:
            txn.commit()

    def _takeOutGarbage(self, oid, txn):
        # take out the garbage.
        referenceCount=self._referenceCount
        referenceCount.delete(oid, txn)
        self._opickle.delete(oid, txn)
        self._current.delete(oid, txn)

        # Remove/decref references
        referenceCount_get=referenceCount.get
        referenceCount_put=referenceCount.put
        c=self._oreferences.cursor(txn)
        try:
            try: roid = c.set(oid)
            except:
                pass
            else:
                while roid:
                    c.delete()
                    roid=roid[1]
                    
                    # decrement refcnt:
                    rc=referenceCount_get(roid, txn)
                    if rc:
                        rc=unpack(">i", rc)[0]-1
                        if rc < 0:
                            raise "Bad reference count, %s" % (rc+1)
                        if rc==0: self._takeOutGarbage(roid, txn)
                        else: referenceCount_put(roid, pack(">i", rc), txn)

                    roid=c.get(db.DB_NEXT_DUP)
        finally: c.close()

        if self._len > 0: self._len=self._len-1


    def pack(self, t, referencesf):
        
        self._lock_acquire()
        try:
            pass
            # TBD
        finally: self._lock_release()


