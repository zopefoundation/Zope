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
""" Base module for BerkeleyStorage implementations """

__version__ ='$Revision: 1.3 $'[11:-2]

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
        self._tempdir = tempfile.tempdir
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
    try:
        if not os.path.exists(name): os.mkdir(name)
    except:
        raise "Error creating BerkeleyDB environment dir: %s" % name
    e=db.DbEnv()
    e.open(name,
           db.DB_CREATE | db.DB_RECOVER
           | db.DB_INIT_MPOOL | db.DB_INIT_LOCK | db.DB_INIT_TXN
           )
    return e
