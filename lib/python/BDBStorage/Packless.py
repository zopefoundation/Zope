##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""
An implementation of a BerkeleyDB-backed storage that uses a reference-
counting garbage-collection strategy which necessitates packing only when
the stored data has cyclically-referenced garbage.
"""

__version__ ='$Revision: 1.6 $'[11:-2]

from base import Base, DBError
from base import BerkeleyDBError
from bsddb3 import db
from struct import pack, unpack
from ZODB.referencesf import referencesf
from ZODB import POSException

MAXTEMPFSIZE = 999999

class ReferenceCountError(POSException.POSError):
    """ An error occured while decrementing a reference to an object in
    the commit phase. The object's reference count was below zero."""

class TemporaryLogCorruptedError(POSException.POSError):
    """ An error occurred due to temporary log file corruption. """

class OutOfTempSpaceError(POSException.POSError):
    """ An out-of-disk-space error occured when writing a temporary log
    file. """


class Packless(Base):

    def _setupDbs(self):
        # Supports Base framework
        self._index=self._setupDB('current')
        self._setupDB('referenceCount')
        self._setupDB('oreferences', flags=db.DB_DUP)
        self._setupDB('opickle')

    def _dbnames(self):
        """
        current -- mapping of oid to current serial
        referenceCount -- mapping of oid to count
        oreferences -- mapping of oid to a sequence of its referenced oids
        opickle -- mapping of oid to pickle
        """
        return 'current', 'referenceCount', 'oreferences', 'opickle'

    def _abort(self):
        pass

    def load(self, oid, version):
        self._lock_acquire()
        try:
            try:
                s=self._index[oid]
                p=self._opickle[oid]
                return p, s # pickle, serial
            except DBError, msg:
                raise BerkeleyDBError, (
                    "%s (%s)" % (BerkeleyDBError.__doc__, msg)
                    )
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
            try:
                # write the metadata to the temp log
                self._tmp.write(oid+pack(">i", len(data)))
                # write the pickle to the temp log
                self._tmp.write(data)
            except IOError:
                raise OutOfTempSpaceError, (
                    "%s (%s)" % (OutOfTempSpaceError.__doc__, self._tempdir)
                    )
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
            oidlen=8 # length in bytes of oid string rep
            intlen=4 # length in bytes of struct.packed integer string rep
            fsize=tmp.tell()
            tmp.seek(0)
            read=tmp.read
            l=0
            while l < fsize:
                sdata = read(oidlen+intlen)
                oid, ldata = unpack(">%ssi" % oidlen, sdata)
                data=read(ldata)

                # get references
                referencesl=[]
                referencesf(data, referencesl)
                references={}
                for roid in referencesl: references[roid]=1
                referenced=references.has_key

                # Create refcnt
                if not referenceCount_get(oid, txn=txn):
                    referenceCount_put(oid, '\0'*intlen, txn=txn)
                    # zeros[oid]=1
                    # ^^^^^^^^^^^^
                    # this should happen when ZODB import is fixed
                    # to commit an import in a subtransaction.  we rely
                    # on pack to get rid of unreferenced objects added
                    # via an aborted import now.  this is only slightly
                    # lame.
                    
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
                                          referenceCount_get(roid,txn=txn))[0]
                                rc=rc-1
                                if rc < 0:
                                    # This should never happen
                                    rce = ReferenceCountError
                                    raise rce, (
                                        "%s (Oid %s had refcount %s)" %
                                        (rce.__doc__,`roid`,rc)
                                        )
                                referenceCount_put(roid, pack(">i", rc), txn)
                                if rc==0: zeros[roid]=1
                            roid=c.get(db.DB_NEXT_DUP)

                finally: c.close()

                # Now add any references that weren't already stored:
                for roid in references.keys():
                    oreferences_put(oid, roid, txn)

                    # Create/update refcnt
                    rcs=referenceCount_get(roid, txn=txn)
                    if rcs:
                        rc=unpack(">i", rcs)[0]
                        if rc==0:
                            try: del zeros[roid]
                            except: pass
                        referenceCount_put(roid, pack(">i", rc+1), txn)
                    else:
                        referenceCount_put(roid, pack(">i", 1), txn)
                
                l=l+ldata+oidlen+intlen
                if ldata > fsize:
                    # this should never happen.
                    raise TemporaryLogCorruptedError, (
                        TemporaryLogCorruptedError.__doc__
                        )
                serial_put(oid, serial, txn)
                opickle_put(oid, data, txn)

            if zeros:
                for oid in zeros.keys():
                    if oid == '\0\0\0\0\0\0\0\0': continue
                    self._takeOutGarbage(oid, txn)
                    
            tmp.seek(0)
            if fsize > MAXTEMPFSIZE: tmp.truncate()

        except DBError, msg:
            try:
                txn.abort()
            except db.error, msg:
                raise BerkeleyDBError, "%s (%s)" % (BerkeleyDBError.__doc__,
                                                    msg)
            raise BerkeleyDBError, "%s (%s)" % (BerkeleyDBError.__doc__,
                                                msg)
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
                    rc=referenceCount_get(roid, txn=txn)
                    if rc:
                        rc=unpack(">i", rc)[0]-1
                        if rc < 0:
                            rce = ReferenceCountError
                            raise rce, (
                                "%s (Oid %s had refcount %s)" %
                                (rce.__doc__,`roid`,rc)
                                )
                        if rc==0: self._takeOutGarbage(roid, txn)
                        else: referenceCount_put(roid, pack(">i", rc), txn)

                    roid=c.get(db.DB_NEXT_DUP)
        finally: c.close()

        if self._len > 0: self._len=self._len-1

    def pack(self, t, referencesf):
        self._lock_acquire()
        try:
            try:
                txn = self._env.txn_begin()
                rindex={}
                referenced=rindex.has_key
                rootl=['\0\0\0\0\0\0\0\0']

                # mark referenced objects
                while rootl:
                    oid=rootl.pop()
                    if referenced(oid): continue
                    p = self._opickle[oid]
                    referencesf(p, rootl)
                    rindex[oid] = None
                    
                # sweep unreferenced objects
                for oid in self._index.keys():
                    if not referenced(oid):
                        self._takeOutGarbage(oid, txn)
            except:
                txn.abort()
                raise
            else:
                txn.commit()
        finally:
            self._lock_release()



    

