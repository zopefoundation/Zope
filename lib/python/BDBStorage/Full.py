from base import Base
from bsddb3 import db
from struct import pack, unpack
import os, tempfile
from ZODB import POSException

def opendb(env, prefix):
    d=db.Db(env)
    d.open(self._prefix+'mini', db.DB_BTREE, db.DB_CREATE)

class Full(Base):
        
    def _setupDbs(self):
        self._index=self._setupDB('current')
        for name in 'pickle', 'record', 'trans', 'vids', 'versions':
            self._setupDB(name)

        self._setupDB('currentVersions', flags=db.DB_DUP)

    def _dbnames(self):
        return ('current', 'pickle', 'record', 'trans',
                'vids', 'versions', 'currentVersions')

    def abortVersion(self, src, transaction):
        
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        c=0
        self._lock_acquire()
        try:
            newtid=self._serial
            vid=self._vids[src]

            oids=[]; save_oid=oids.append
            c=self._currentVersions.cursor()
            i=c.set(vid)
            get=c.get
            current=self._current
            records=self._record
            tmp=self._tmp
            dump=marshal.dump
            zero="\0\0\0\0\0\0\0\0"
            while i:
                v, oid = i

                # Get current record data
                tid=current[oid]
                record=records[oid+tid]
                rvid, nv, data = unpack("8s8s8s", record[:24])
                if rvid != vid: raise "vid inconsistent with currentVersions"
                if nv == zero: continue

                # Get non-version data
                record=records[oid+nv]
                rvid, nv, data = unpack("8s8s8s", record[:24])
                if rvid: raise "expected non-version data"

                dump(('s',(oid,zero,zero,data,'',tid)), tmp)

                save_oid(oid)
                
                i=get(db.DB_NEXT_DUP)

            dump(('v',vid),tmp)
            self._vtmp[vid]='a'

            return oids
        finally:
            if c != 0: c.close()
            self._lock_release()

    def commitVersion(self, src, dest, transaction):
        
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        c=0
        self._lock_acquire()
        try:
            newtid=self._serial
            vid=self._vids[src]
            try: dvid=self._vids[dest]
            except KeyError: dvid=self._newvid(dest)

            oids=[]; save_oid=oids.append
            c=self._currentVersions.cursor()
            i=c.set(vid)
            get=c.get
            current=self._current
            records=self._record
            tmp=self._tmp
            dump=marshal.dump
            zero="\0\0\0\0\0\0\0\0"
            while i:
                v, oid = i

                # Get current record data
                tid=current[oid]
                record=records[oid+tid]
                rvid, nv, data = unpack("8s8s8s", record[:24])
                if rvid != vid: raise "vid inconsistent with currentVersions"

                if not dest: nv=zero
                dump(('s',(oid,dvid,nv,data,'',tid)), tmp)

                save_oid(oid)
                
                i=get(db.DB_NEXT_DUP)

            dump(('d',vid),tmp)
            self._vtmp[vid]='c'
            if dest: self._vtmp[dvid]='d'

            return oids
        finally:
            if c != 0: c.close()
            self._lock_release()

    def load(self, oid, version):
        self._lock_acquire()
        try:
            t=self._index[oid]
            vid, nv, data = unpack(">8s8s8s", self._record[oid+t][:24])
            if vid == '\0\0\0\0\0\0\0\0' or self._versions[vid]==version:
                return self._pickle[oid+data], t
            t=nv
            data = self._record[oid+t][16:24]
            return self._pickle[oid+data], t
        finally: self._lock_release()

    def loadSerial(self, oid, serial):
        self._lock_acquire()
        try:
            data = self._record[oid+serial][16:24]
            return self._pickle[oid+data]
        finally: self._lock_release()
                                
    def modifiedInVersion(self, oid):
        self._lock_acquire()
        try:
            t=self._index[oid]
            vid = self._record[oid+t][:8]
            if vid == '\0\0\0\0\0\0\0\0': return ''
            return self._versions[vid]
        finally: self._lock_release()

    def store(self, oid, serial, data, version, transaction):
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        self._lock_acquire()
        try:
            if version:
                try: vid=self._vids[version]
                except:
                    vid=self._newvid()

            else:
                vid=nv='\0\0\0\0\0\0\0\0'

            if self._index.has_key(oid):
                old=self._index[oid]
                if serial != old: raise POSException.ConflictError
                ovid, nv = unpack(">8s8s", self._record[oid+old][:16])
                            
                if ovid != vid:
                    raise POSException.VersionLockError, (`oid`, ovid)
            
                if version and ovid == '\0\0\0\0\0\0\0\0': nv=old
            else:
                nv='\0\0\0\0\0\0\0\0'

            dump(('s',(oid, vid, nv, '', data, old)), self._tmp)
            
        finally: self._lock_release()

        return serial

    def supportsUndo(self): return 1
    def supportsVersions(self): return 1

    def _finish(self, tid, u, d, e):
        txn = self._env.txn_begin()
        try:
            tmp=self._tmp
            ltmp=tmp.tell()
            if not ltmp: return
            load=marshal.load
            tid=self._serial
            records_put=self._records.put
            pickles_put=self._pickle.put
            current_put=self._current.put
            currentVersions_put=self._currentVersions.put
            l=pack(">HI",len(u), len(d))
            self._trans.put(tid, l+u+d+e, txn)
            while ltmp:
                try: op, arg = load(tmp)
                except EOFError:
                    if tmp.tell()==ltmp: ltmp=0
                    else: raise
                else:
                    if op=='s':
                        oid, vid, nv, back, data, pre = arg
                        key=oid+tid
                        if data:
                            pickles_pud(key, data, txn)
                            data=tid
                        else:
                            data=back
                        records_put(key, vid+nv+data+pre, txn)
                        if vid != '/0/0/0/0/0/0/0/0':
                            versions_put(vid, oid, txn)
                        current_put(oid, tid, txn)
                    elif op='d':
                        self._currentVersions.delete(arg, txn)
                    elif op='v':
                        
        except:
            txn.abort()
        else:
            txn.commit()




    def tpc_vote(self, transaction):
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        self._lock_acquire()
        try:
            txn = self._txn = self._env.txn_begin()
            put=self._index.put
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
                put(oid, serial+data, txn)

            tmp.seek(0)
            if s > 999999: tmp.truncate()
            
        finally: self._lock_release()

    def pack(self, t, referencesf):
        
        self._lock_acquire()
        try:    
            # Build an index of *only* those objects reachable
            # from the root.
            index=self._index
            rootl=['\0\0\0\0\0\0\0\0']
            pop=rootl.pop
            pindex={}
            referenced=pindex.has_key
            while rootl:
                oid=pop()
                if referenced(oid): continue
    
                # Scan non-version pickle for references
                r=index[oid]
                pindex[oid]=r
                p=r[8:]
                referencesf(p, rootl)

            # Now delete any unreferenced entries:
            for oid in index.keys():
                if not referenced(oid): del index[oid]
    
        finally: self._lock_release()


