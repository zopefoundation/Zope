from base import Base
from bsddb3 import db
from struct import pack, unpack
import os, tempfile, string, marshal
from ZODB import POSException, utils
from marshal import dump, load

class Full(Base):
        
    def _setupDbs(self):
        # Supports Base framework
        self._index=self._setupDB('current')
        for name in 'pickle', 'record', 'transactions', 'vids', 'versions':
            self._setupDB(name)

        self._setupDB('currentVersions', flags=db.DB_DUP)
        self._setupDB('transaction_oids', flags=db.DB_DUP)

        c=self._vids.cursor()
        v=c.get(db.DB_LAST)
        if v: self._vid=utils.U64(v[0])
        else: self._vid=0L
        

    def _dbnames(self):
        # Supports Base framework
        return ('current', 'pickle', 'record',
                'transactions', 'transaction_oids',
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

            oids=[]; save_oid=oids.append
            c=self._currentVersions.cursor()
            i=c.set(vid)
            get=c.get
            current=self._current
            records=self._record
            tmp=self._tmp
            dump=marshal.dump
            zero="\0\0\0\0\0\0\0\0"

            try: dvid=self._vids[dest]
            except KeyError:
                dvid=self._newvid()
                dump(('v',(vid, version)), tmp)

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
            tid=self._current[oid]
            vid=self._record[oid+tid][:8]
            if vid == '\0\0\0\0\0\0\0\0': return ''
            return self._versions[vid]
        finally: self._lock_release()

    def _newvid(self):
        self._vid=self._vid+1
        return utils.p64(self._vid)

    def store(self, oid, serial, data, version, transaction):
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        self._lock_acquire()
        try:
            if version:
                try: vid=self._vids[version]
                except:
                    vid=self._newvid()
                    dump(('v',(vid, version)), self._tmp)

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
        txn=self._env.txn_begin()
        try:
            tmp=self._tmp
            ltmp=tmp.tell()
            if not ltmp: return
            load=marshal.load
            tid=self._serial
            records_put=self._records.put
            pickles_put=self._pickle.put
            current_put=self._current.put
            transaction_oids_put=self._transaction_oids.put
            currentVersions_put=self._currentVersions.put
            l=pack(">HI",len(u), len(d))
            self._transactions.put(tid, ' '+l+u+d+e, txn)
            while ltmp:
                try: op, arg = load(tmp)
                except EOFError:
                    if tmp.tell()==ltmp: ltmp=0
                    else: raise
                else:
                    if op=='s':
                        # store data
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
                        transaction_oids_put(tid, oid, txn)
                    elif op='d':
                        # discard a version (part of version commit and abort)
                        self._currentVersions.delete(arg, txn)
                    elif op='v':
                        # save a version definition
                        vid, version = arg
                        self._versions.put(vid, version, txn)
                        self._vids.put(version, vid, txn)
                        
        except:
            txn.abort()
            raise
        else:
            txn.commit()

    def _undoable(self, txn):
        txn.abort()
        raise POSException.UndoError, 'Undoable transaction'
        
    def undo(self, tid):
        self._lock_acquire()
        try:
            status = self._transactions[tid][:1]
            if status == 'p': 
                raise POSException.UndoError, 'Undoable transaction'
            
            txn=self._env.txn_begin()

            current=self._current
            record=self._record
            pickle=self._pickle
            currentVersions=self._currentVersions
            unpack=struct.unpack

            try:
                for oid in dups(self._transaction_oids, tid, txn):
                    if current.get(oid, txn) != tid: self._undoable(txn)
                    key=oid+tid
                    vid, nv, data, pre = unpack("8s8s8s8s",
                                                record.get(key, txn))
                    record.delete(key, txn)
                    if data==tid: pickle.delete(key, txn)
                    if pre == '\0\0\0\0\0\0\0\0':
                        current.delete(oid, txn)
                    else:
                        current.put(oid, pre, txn)
                        try: pvid=record.get(oid+pre, txn)
                        except KeyError: self._undoable(txn)
                        if pvid != vid:
                            if vid != '\0\0\0\0\0\0\0\0':
                                del_dup(currentVersions, vid, oid, txn)
                            if pvid != '\0\0\0\0\0\0\0\0':
                                currentVersions.put(pvid, oid, txn)

                self._transactions.delete(tid, txn)
                self._transaction_oids.delete(tid, txn)
            except:
                txn.abort()
                raise
            else:
                txn.commit()
            
        finally: self._lock_release()

    def undoLog(self, first, last, filter=None):
        self._lock_acquire()
        try:
            c=self._transactions.cursor()
            try:
                i=0; r=[]; a=r.append
                data=c.get(db.DB_LAST)
                while data and i < last:
                    tid, data = data
                    status = data[:1]
                    if status == 'p': break
                    luser, ldesc = unpack("HI", data[1:17])
                    user=data[17:luser+17]
                    desc=data[luser+17:luser+17+ldesc]
                    ext=data[luser+17+ldesc:]

                    data={'id': tid,
                          'time': TimeStamp(tid).timeTime(),
                          'user_name': user or '',
                          'description': desc or '',
                          }
                    if ext:
                        try: 
                            ext=loads(ext)
                            data.update(ext)
                        except: pass

                    if filter is None or filter(data):
                        if i >= first: a(data)
                        i=i+1

                    data=c.get(db.DB_PREV)

                return r
        
            finally: c.close()
        finally: self._lock_release()

    def versionEmpty(self, version):
        self._lock_acquire()
        try:
            try: self._currentVersions[self._vids[version]]
            except KeyError: return 1
            else: return 0
        finally: self._lock_release()

    def versions(self, max=None):
        self._lock_acquire()
        try:
            c=self._currentVersions.cursor()
            try:
                try: data=c.get(db.DB_NEXT_NODUP)
                except: return ()
                r=[]; a=r.append
                while data:
                    a(data[0])
                    data=c.get(db.DB_NEXT_NODUP)
                    
                return r
        
            finally: c.close()
        finally: self._lock_release()

    def history(self, oid, version=None, length=1, filter=None):
        self._lock_acquire()
        try:
            tid=self._current[oid]
            
            
        finally: self._lock_release()


    def pack(self, t, referencesf):
        
        self._lock_acquire()
        try:    
    
        finally: self._lock_release()


class dups:
    """Iterator for duplicate-record databases"

    def __init__(self, db, key, txn=0):
        if txn==0:
            c=db.cursor()
        else:
            c=db.cursor(txn)
        self._v=c.set(key)
        self._g=c.get
        self._i=0

    def __getitem__(self, index):
        i=self._i
        if index==i: return self._v
        if index < i or i < 0: raise IndexError, index
        while i < index:
            v=self._g(db.DB_NEXT_DUP)
            if v:
                i=i+1
            else:
                self._i=-1
                raise IndexError, index

        self._i=i
        self._v=v
        return v

def del_dup(database, key, value, txn):
    c=database.cursor(txn)
    try:
        c.getBoth(key, value)
        c.delete()
    finally:
        c.close()
        
    
