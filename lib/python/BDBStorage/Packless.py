##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""
An implementation of a BerkeleyDB-backed storage that uses a reference-
counting garbage-collection strategy which necessitates packing only when
the stored data has cyclically-referenced garbage.
"""

__version__ ='$Revision: 1.3 $'[11:-2]

from base import Base
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
            try:
                # write the metadata to the temp log
                self._tmp.write(oid+pack(">i", len(data)))
                # write the pickle to the temp log
                self._tmp.write(data)
            except IOError:
                raise OutOfTempSpaceError, self._tempdir
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
                if not referenceCount_get(oid, txn):
                    referenceCount_put(oid, '\0'*intlen, txn)
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
                                          referenceCount_get(roid, txn))[0]
                                rc=rc-1
                                if rc < 0:
                                    # This should never happen
                                     raise ReferenceCountError, (
                                        "Oid %s had refcount %s" % (`roid`,rc)
                                        )
                                referenceCount_put(roid, pack(">i", rc), txn)
                                if rc==0: zeros[roid]=1
                            roid=c.get(db.DB_NEXT_DUP)

                finally: c.close()

                # Now add any references that weren't already stored:
                for roid in references.keys():
                    oreferences_put(oid, roid, txn)

                    # Create/update refcnt
                    rcs=referenceCount_get(roid, txn)
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
                    raise TemporaryLogCorruptedError
                serial_put(oid, serial, txn)
                opickle_put(oid, data, txn)

            if zeros:
                for oid in zeros.keys():
                    if oid == '\0\0\0\0\0\0\0\0': continue
                    self._takeOutGarbage(oid, txn)
                    
            tmp.seek(0)
            if fsize > MAXTEMPFSIZE: tmp.truncate()

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
                            raise ReferenceCountError, (
                                "Oid %s had refcount %s" % (`roid`,rc)
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



    

