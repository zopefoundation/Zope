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
A storage implementation which uses RAM to persist objects, much like
MappingStorage.  Unlike MappingStorage, it needs not be packed to get rid of
non-cyclic garbage and it does rudimentary conflict resolution.  This is a
ripoff of Jim's Packless bsddb3 storage.

$Id: TemporaryStorage.py,v 1.5 2001/11/26 15:34:56 chrism Exp $
"""

__version__ ='$Revision: 1.5 $'[11:-2]

from zLOG import LOG
from ZODB.referencesf import referencesf
from ZODB import POSException
from ZODB.BaseStorage import BaseStorage
from ZODB.ConflictResolution import ConflictResolvingStorage, ResolvedSerial
import time

# keep old object revisions for CONFLICT_CACHE_MAXAGE seconds
CONFLICT_CACHE_MAXAGE = 60
# garbage collect conflict cache every CONFLICT_CACHE_GCEVERY seconds
CONFLICT_CACHE_GCEVERY = 60

class ReferenceCountError(POSException.POSError):
    """ An error occured while decrementing a reference to an object in
    the commit phase. The object's reference count was below zero."""

class TemporaryStorageError(POSException.POSError):
    """ A Temporary Storage exception occurred.  This probably indicates that
    there is a low memory condition or a tempfile space shortage.  Check
    available tempfile space and RAM consumption and restart the server
    process."""

class TemporaryStorage(BaseStorage, ConflictResolvingStorage):

    def __init__(self, name='TemporaryStorage'):
        """
        index -- mapping of oid to current serial
        referenceCount -- mapping of oid to count
        oreferences -- mapping of oid to a sequence of its referenced oids
        opickle -- mapping of oid to pickle
        _tmp -- used by 'store' to collect changes before finalization
        _conflict_cache -- cache of recently-written object revisions
        _last_cache_gc -- last time that conflict cache was garbage collected
        """
        BaseStorage.__init__(self, name)

        self._index={}
        self._referenceCount={}
        self._oreferences={}
        self._opickle={}
        self._tmp = []
        self._conflict_cache = {}
        self._last_cache_gc = 0
        self._oid = '\0\0\0\0\0\0\0\0'

    def __len__(self):
        return len(self._index)

    def getSize(self):
        return 0

    def _clear_temp(self):
        now = time.time()
        if now > (self._last_cache_gc + CONFLICT_CACHE_GCEVERY):
            for k, v in self._conflict_cache.items():
                data, t = v
                if now > (t + CONFLICT_CACHE_MAXAGE):
                    del self._conflict_cache[k]
            self._last_cache_gc = now
        self._tmp = []
        
    def close(self):
        """
        Close the storage
        """
    
    def load(self, oid, version):
        self._lock_acquire()
        try:
            s=self._index[oid]
            p=self._opickle[oid]
            return p, s # pickle, serial
        finally:
            self._lock_release()

    def loadSerial(self, oid, serial, marker=[]):
        """ this is only useful to make conflict resolution work.  It
        does not actually implement all the semantics that a revisioning
        storage needs! """
        self._lock_acquire()
        try:
            data, t = self._conflict_cache.get((oid, serial), marker)
            if data is marker:
                raise POSException.ConflictError, (oid, serial)
            return data
        finally:
            self._lock_release()
            
    def store(self, oid, serial, data, version, transaction):
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)
        if version:
            raise POSException.Unsupported, (
                "TemporaryStorage is incompatible with versions"
                )
        self._lock_acquire()
        try:
            if self._index.has_key(oid):
                oserial=self._index[oid]
                if serial != oserial:
                    data=self.tryToResolveConflict(oid, oserial, serial, data)
                    if not data:
                        raise POSException.ConflictError, (serial,oserial)
            else:
                oserial = serial
            newserial=self._serial
            self._tmp.append((oid, data))
            now = time.time()
            self._conflict_cache[(oid, newserial)] = data, now
            return serial == oserial and newserial or ResolvedSerial
        finally:
            self._lock_release()

    def _finish(self, tid, u, d, e):
        zeros={}
        referenceCount=self._referenceCount
        referenceCount_get=referenceCount.get
        oreferences=self._oreferences
        serial=self._serial
        index=self._index
        opickle=self._opickle

        # iterate over all the objects touched by/created within this
        # transaction
        for entry in self._tmp:
            oid, data = entry[:]
            referencesl=[]
            referencesf(data, referencesl)
            references={}
            for roid in referencesl:
                references[roid]=1
            referenced=references.has_key

            # Create a reference count for this object if one
            # doesn't already exist
            if referenceCount_get(oid) is None:
                referenceCount[oid] = 0
                #zeros[oid]=1

            # update references that are already associated with this
            # object
            roids = oreferences.get(oid, [])
            for roid in roids:
                if referenced(roid):
                    # still referenced, so no need to update
                    # remove it from the references dict so it doesn't
                    # get "added" in the next clause
                    del references[roid]
                else:
                    # Delete the stored ref, since we no longer
                    # have it
                    oreferences[oid].remove(roid)
                    # decrement refcnt:
                    rc = referenceCount_get(roid, 1)
                    rc=rc-1
                    if rc < 0:
                        # This should never happen
                        raise ReferenceCountError, (
                            "%s (Oid %s had refcount %s)" %
                            (ReferenceCountError.__doc__,`roid`,rc)
                            )
                    referenceCount[roid] = rc
                    if rc==0:
                        zeros[roid]=1

            # Create a reference list for this object if one
            # doesn't already exist
            if oreferences.get(oid) is None:
                oreferences[oid] = []

            # Now add any references that weren't already stored
            for roid in references.keys():
                oreferences[oid].append(roid)
                # Create/update refcnt
                rc=referenceCount_get(roid, 0)
                if rc==0 and zeros.get(roid) is not None:
                    del zeros[roid]
                referenceCount[roid] = rc+1

            index[oid] =  serial
            opickle[oid] = data

        if zeros:
            for oid in zeros.keys():
                if oid == '\0\0\0\0\0\0\0\0': continue
                self._takeOutGarbage(oid)

        self._tmp = []
        
    def _takeOutGarbage(self, oid):
        # take out the garbage.
        referenceCount=self._referenceCount
        referenceCount_get=referenceCount.get
        try: del referenceCount[oid]
        except: pass
        try: del self._opickle[oid]
        except: pass
        try: del self._index[oid]
        except: pass

        # Remove/decref references
        roids = self._oreferences.get(oid, [])
        while roids:
            roid = roids.pop(0)
            # decrement refcnt:
            rc=referenceCount_get(roid, 0)
            if rc==0:
                self._takeOutGarbage(roid)
            elif rc < 0:
                raise ReferenceCountError, (
                    "%s (Oid %s had refcount %s)" %
                    (ReferenceCountError.__doc__,`roid`,rc)
                    )
            else:
                referenceCount[roid] = rc - 1
        try: del self._oreferences[oid]
        except: pass
                
    def pack(self, t, referencesf):
        self._lock_acquire()
        try:
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
                    self._takeOutGarbage(oid)
        finally:
            self._lock_release()


    

    

