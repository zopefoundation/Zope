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

"""Base class for BerkeleyStorage implementations.
"""

import os
import errno
from types import StringType

# This uses the Dunn/Kuchling PyBSDDB v3 extension module available from
# http://pybsddb.sourceforge.net
from bsddb3 import db

# BaseStorage provides some common storage functionality.  It is derived from
# UndoLogCompatible.UndoLogCompatible, which "[provides] backward
# compatability with storages that have undoLog, but not undoInfo."
#
# BAW: I'm not entirely sure what that means, but the UndoLogCompatible
# subclass provides one method:
#
# undoInfo(first, last, specification).  Unfortunately this method appears to
# be undocumented.  Jeremy tells me it's still required though.
#
# BaseStorage provides primitives for lock acquisition and release,
# abortVersion(), commitVersion() and a host of other methods, some of which
# are overridden here, some of which are not.
from ZODB import POSException
from ZODB.BaseStorage import BaseStorage

__version__ = '$Revision: 1.17 $'.split()[-2:][0]



class BerkeleyBase(BaseStorage):
    """Base storage for Minimal and Full Berkeley implementations."""

    def __init__(self, name, env=None, prefix='zodb_'):
        """Create a new storage.

        name is an arbitrary name for this storage.  It is returned by the
        getName() method.

        Optional env, if given, is either a string or a DBEnv object.  If it
        is a non-empty string, it names the database environment,
        i.e. essentially the name of a directory into which BerkeleyDB will
        store all its supporting files.  It is passed directly to
        DbEnv().open(), which in turn is passed to the BerkeleyDB function
        DBEnv->open() as the db_home parameter.

        Note that if you want to customize the underlying Berkeley DB
        parameters, this directory can contain a DB_CONFIG file as per the
        Sleepycat documentation.

        If env is given and it is not a string, it must be an opened DBEnv
        object as returned by bsddb3.db.DBEnv().  In this case, it is your
        responsibility to create the object and open it with the proper
        flags.

        Optional prefix is the string to prepend to name when passed to
        DB.open() as the dbname parameter.  IOW, prefix+name is passed to the
        BerkeleyDb function DB->open() as the database parameter.  It defaults
        to "zodb_".
        """

        # sanity check arguments
        if name == '':
            raise TypeError, 'database name is empty'

        if env is None:
            env = name

        if env == '':
            raise TypeError, 'environment name is empty'
        elif isinstance(env, StringType):
            self._env = env_from_string(env)
        else:
            self._env = env

        BaseStorage.__init__(self, name)

        # Initialize a few other things
        self._prefix = prefix
        self._commitlog = None
        # Give the subclasses a chance to interpose into the database setup
        # procedure
        self._setupDBs()
        # Initialize the object id counter.
        self._init_oid()

    def _closelog(self):
        if self._commitlog:
            self._commitlog.finish()
            # JF: unlinking might be too inefficient.  JH: might use mmap
            # files.  BAW: maybe just truncate the file, or write a length
            # into the headers and just zero out the length.
            self._commitlog.close(unlink=1)
            self._commitlog = None
        
    def _setupDB(self, name, flags=0):
        """Open an individual database with the given flags.

        flags are passed directly to the underlying DB.set_flags() call.
        """
        d = db.DB(self._env)
        if flags:
            d.set_flags(flags)
        # Our storage is based on the underlying BSDDB btree database type.
        d.open(self._prefix + name, db.DB_BTREE, db.DB_CREATE)
        return d

    def _setupDBs(self):
        """Set up the storages databases, typically using '_setupDB'.

        This must be implemented in a subclass.
        """
        raise NotImplementedError, '_setupDbs()'

    def _init_oid(self):
        """Initialize the object id counter."""
        # If the `serials' database is non-empty, the last object id in the
        # database will be returned (as a [key, value] pair).  Use it to
        # initialize the object id counter.
        #
        # If the database is empty, just initialize it to zero.
        value = self._serials.cursor().last()
        if value:
            self._oid = value[0]
        else:
            self._oid = '\0\0\0\0\0\0\0\0'

    # It can be very expensive to calculate the "length" of the database, so
    # we cache the length and adjust it as we add and remove objects.
    _len = None

    def __len__(self):
        """Return the number of objects in the index."""
        if self._len is None:
            # The cache has never been initialized.  Do it once the expensive
            # way.
            self._len = len(self._serials)
        return self._len

    def new_oid(self, last=None):
        """Create a new object id.

        If last is provided, the new oid will be one greater than that.
        """
        # BAW: the last parameter is undocumented in the UML model
        if self._len is not None:
            # Increment the cached length
            self._len = self._len + 1
        return BaseStorage.new_oid(self, last)

    def getSize(self):
        """Return the size of the database."""
        # Return the size of the pickles table as a rough estimate
        filename = os.path.join(self._env.db_home, 'zodb_pickles')
        return os.path.getsize(filename)

    # BAW: this overrides BaseStorage.tpc_vote() with exactly the same
    # implementation.  This is so Zope 2.3.1, which doesn't include the change
    # to BaseStorage, will work with Berkeley.  Once we can ignore older
    # versions of ZODB, we can get rid of this.
    def tpc_vote(self, transaction):
        self._lock_acquire()
        try:
            if transaction is not self._transaction: return
            self._vote()
        finally:
            self._lock_release()

    def _vote(self):
        # Make a promise to commit all the registered changes.  Rewind and put
        # our commit log in the PROMISED state.
        self._commitlog.promise()

    def _finish(self, tid, user, desc, ext):
        """Called from BaseStorage.tpc_finish(), this commits the underlying
        BSDDB transaction.

        tid is the transaction id
        user is the transaction user
        desc is the transaction description
        ext is the transaction extension

        These are all ignored.
        """
        self._transaction.commit()

    def _abort(self):
        """Called from BaseStorage.tpc_abort(), this aborts the underlying
        BSDDB transaction.
        """
        self._closelog()
        self._transaction.abort()

    def _clear_temp(self):
        """Called from BaseStorage.tpc_abort(), BaseStorage.tpc_begin(),
        BaseStorage.tpc_finish(), this clears out the temporary log file
        """
        # BAW: no-op this since the right CommitLog file operations are
        # performed by the methods in the derived storage class.
        pass

    def close(self):
        """Close the storage by closing the databases it uses and by closing
        its environment.
        """
        # As recommended by Keith Bostic @ Sleepycat, we need to do
        # two checkpoints just before we close the environment.
        # Otherwise, auto-recovery on environment opens can be
        # extremely costly.  We want to do auto-recovery for ease of
        # use, although they aren't strictly necessary if the database
        # was shutdown gracefully.  The DB_FORCE flag is required for
        # the second checkpoint, but we include it in both because it
        # can't hurt and is more robust.
	self._env.txn_checkpoint(0, 0, db.DB_FORCE)
	self._env.txn_checkpoint(0, 0, db.DB_FORCE)
        self._env.close()
        self._closelog()



def env_from_string(envname):
    # BSDDB requires that the directory already exists.  BAW: do we need to
    # adjust umask to ensure filesystem permissions?
    try:
        os.mkdir(envname)
    except OSError, e:
        if e.errno <> errno.EEXIST: raise
        # already exists
    env = db.DBEnv()
    env.open(envname,
             db.DB_CREATE       # create underlying files as necessary
             | db.DB_RECOVER    # run normal recovery before opening
             | db.DB_INIT_MPOOL # initialize shared memory buffer pool
             | db.DB_INIT_LOCK  # initialize locking subsystem
             | db.DB_INIT_TXN   # initialize transaction subsystem
             | db.DB_THREAD     # we use the environment from other threads
             )
    return env
