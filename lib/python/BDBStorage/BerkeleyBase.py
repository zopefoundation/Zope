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
__version__ = '$Revision: 1.30 $'.split()[-2:][0]

import os
import time
import errno
import select
import threading
from types import StringType

# This uses the Dunn/Kuchling PyBSDDB v3 extension module available from
# http://pybsddb.sourceforge.net
from bsddb3 import db

# BaseStorage provides primitives for lock acquisition and release, and a host
# of other methods, some of which are overridden here, some of which are not.
from ZODB.lock_file import lock_file
from ZODB.BaseStorage import BaseStorage
from ZODB.referencesf import referencesf
import ThreadLock
import zLOG

GBYTES = 1024 * 1024 * 1000

# How long should we wait to join one of the background daemon threads?  It's
# a good idea to not set this too short, or we could corrupt our database.
# That would be recoverable, but recovery could take a long time too, so it's
# better to shutdown cleanly.
JOIN_TIME = 10

try:
    True, False
except NameError:
    True = 1
    False = 0



class PackStop(Exception):
    """Escape hatch for pack operations."""



class BerkeleyConfig:
    """Bag of bits for describing various underlying configuration options.

    Berkeley databases are wildly configurable, and this class exposes some of
    that.  To customize these options, instantiate one of these classes and
    set the attributes below to the desired value.  Then pass this instance to
    the Berkeley storage constructor, using the `config' keyword argument.

    Berkeley storages need to be checkpointed occasionally, otherwise
    automatic recover can take a huge amount of time.  You should set up a
    checkpointing policy which trades off the amount of work done periodically
    against the recovery time.  Note that the Berkeley environment is
    automatically, and forcefully, checkpointed twice when it is closed.

    The following checkpointing attributes are supported:

    - interval indicates how often, in seconds, a Berkeley checkpoint is
      performed.  If this is non-zero, checkpointing is performed by a
      background thread.  Otherwise checkpointing will only be done when the
      storage is closed.   You really want to enable checkpointing. ;)

    - kbytes is passed directly to txn_checkpoint()

    - min is passed directly to txn_checkpoint()

    You can acheive one of the biggest performance wins by moving the Berkeley
    log files to a different disk than the data files.  We saw between 2.5 and
    7 x better performance this way.  Here are attributes which control the
    log files.

    - logdir if not None, is passed to the environment's set_lg_dir() method
      before it is opened.

    You can also improve performance by tweaking the Berkeley cache size.
    Berkeley's default cache size is 256KB which is usually too small.  Our
    default cache size is 128MB which seems like a useful tradeoff between
    resource consumption and improved performance.  You might be able to get
    slightly better results by turning up the cache size, although be mindful
    of your system's limits.  See here for more details:

        http://www.sleepycat.com/docs/ref/am_conf/cachesize.html

    These attributes control cache size settings:

    - cachesize should be the size of the cache in bytes.

    These attributes control the autopacking thread:

    - frequency is the time in seconds after which an autopack phase will be
      performed.  E.g. if frequency is 3600, an autopack will be done once per
      hour.  Set frequency to 0 to disable autopacking (the default).

    - packtime is the time in seconds marking the moment in the past at which
      to autopack to.  E.g. if packtime is 14400, autopack will pack to 4
      hours in the past.  For Minimal storage, this value is ignored.

    - classicpack is an integer indicating how often an autopack phase should
      do a full classic pack.  E.g. if classicpack is 24 and frequence is
      3600, a classic pack will be performed once per day.  Set to zero to
      never automatically do classic packs.  For Minimal storage, this value
      is ignored -- all packs are classic packs.
    """
    interval = 120
    kbyte = 0
    min = 0
    logdir = None
    cachesize = 128 * 1024 * 1024
    frequency = 0
    packtime = 4 * 60 * 60
    classicpack = 0



class BerkeleyBase(BaseStorage):
    """Base storage for Minimal and Full Berkeley implementations."""

    def __init__(self, name, env=None, prefix='zodb_', config=None):
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

        Optional config must be a BerkeleyConfig instance, or None, which
        means to use the default configuration options.
        """
        # sanity check arguments
        if config is None:
            config = BerkeleyConfig()
        self._config = config

        if name == '':
            raise TypeError, 'database name is empty'

        if env is None:
            env = name

        if env == '':
            raise TypeError, 'environment name is empty'
        elif isinstance(env, StringType):
            self._env, self._lockfile = env_from_string(env, self._config)
        else:
            self._env = env

        # Use the absolute path to the environment directory as the name.
        # This should be enough of a guarantee that sortKey() -- which via
        # BaseStorage uses the name -- is globally unique.
        envdir = os.path.abspath(self._env.db_home)
        BaseStorage.__init__(self, envdir)

        # Instantiate a pack lock
        self._packlock = ThreadLock.allocate_lock()
        self._stop = self._closed = False
        # Initialize a few other things
        self._prefix = prefix
        # Give the subclasses a chance to interpose into the database setup
        # procedure
        self._tables = []
        self._setupDBs()
        # Initialize the object id counter.
        self._init_oid()
        # Set up the checkpointing thread
        if config.interval > 0:
            r, self._checkpointfd = os.pipe()
            poll = select.poll()
            poll.register(r, select.POLLIN)
            self._checkpointer = _Checkpoint(self, poll, config.interval)
            self._checkpointer.start()
        else:
            self._checkpointer = None
        # Set up the autopacking thread
        if config.frequency > 0:
            r, self._autopackfd = os.pipe()
            poll = select.poll()
            poll.register(r, select.POLLIN)
            self._autopacker = self._make_autopacker(poll)
            self._autopacker.start()
        else:
            self._autopacker = None

    def _make_autopacker(self, poll):
        raise NotImplementedError

    def _setupDB(self, name, flags=0, dbtype=db.DB_BTREE, reclen=None):
        """Open an individual database with the given flags.

        flags are passed directly to the underlying DB.set_flags() call.
        Optional dbtype specifies the type of BerkeleyDB access method to
        use.  Optional reclen if not None gives the record length.
        """
        d = db.DB(self._env)
        if flags:
            d.set_flags(flags)
        # Our storage is based on the underlying BSDDB btree database type.
        if reclen is not None:
            d.set_re_len(reclen)
        openflags = db.DB_CREATE
        # DB 4.1.24 requires that operations happening in a transaction must
        # be performed on a database that was opened in a transaction.  Since
        # we do the former, we must do the latter.  However, earlier DB
        # versions don't transactionally protect database open, so this is the
        # most portable way to write the code.
        try:
            openflags |= db.DB_AUTO_COMMIT
        except AttributeError:
            pass
        d.open(self._prefix + name, dbtype, openflags)
        self._tables.append(d)
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
            self._len += 1
        return BaseStorage.new_oid(self, last)

    def getSize(self):
        """Return the size of the database."""
        # Return the size of the pickles table as a rough estimate
        filename = os.path.join(self._env.db_home, 'zodb_pickles')
        return os.path.getsize(filename)

    def _vote(self):
        pass

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
        self._transaction.abort()

    def _clear_temp(self):
        """Called from BaseStorage.tpc_abort(), BaseStorage.tpc_begin(),
        BaseStorage.tpc_finish(), this clears out the temporary log file
        """
        # BAW: no-op this since the right CommitLog file operations are
        # performed by the methods in the derived storage class.
        pass

    def log(self, msg, *args):
        zLOG.LOG(self.__class__.__name__, zLOG.INFO, msg % args)

    def close(self):
        """Close the storage.

        All background threads are stopped and joined first, then all the
        tables are closed, and finally the environment is force checkpointed
        and closed too.
        """
        # We have to shutdown the background threads before we acquire the
        # lock, or we'll could end up closing the environment before the
        # autopacking thread exits.
        self._stop = True
        # Stop the autopacker thread
        if self._autopacker:
            self.log('stopping autopacking thread')
            self._autopacker.stop()
            os.write(self._autopackfd, 'STOP')
            self._autopacker.join(JOIN_TIME)
        if self._checkpointer:
            self.log('stopping checkpointing thread')
            self._checkpointer.stop()
            os.write(self._checkpointfd, 'STOP')
            self._checkpointer.join(JOIN_TIME)
        self._lock_acquire()
        try:
            if not self._closed:
                self._doclose()
                self._closed = True
        finally:
            self._lock_release()

    def _doclose(self):
        # Close all the tables
        for d in self._tables:
            d.close()
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
        lockfile = os.path.join(self._env.db_home, '.lock')
        self._lockfile.close()
        self._env.close()
        os.unlink(lockfile)

    def _update(self, deltas, data, incdec):
        refdoids = []
        referencesf(data, refdoids)
        for oid in refdoids:
            rc = deltas.get(oid, 0) + incdec
            if rc == 0:
                # Save space in the dict by zapping zeroes
                del deltas[oid]
            else:
                deltas[oid] = rc

    def _withlock(self, meth, *args):
        self._lock_acquire()
        try:
            return meth(*args)
        finally:
            self._lock_release()

    def _withtxn(self, meth, *args, **kws):
        txn = self._env.txn_begin()
        try:
            ret = meth(txn, *args, **kws)
        except PackStop:
            # Escape hatch for shutdown during pack.  Like the bare except --
            # i.e. abort the transaction -- but swallow the exception.
            txn.abort()
        except:
            #import traceback ; traceback.print_exc()
            txn.abort()
            raise
        else:
            txn.commit()
            return ret

    def docheckpoint(self):
        config = self._config
        self._lock_acquire()
        try:
            if not self._stop:
                self._env.txn_checkpoint(config.kbyte, config.min)
        finally:
            self._lock_release()



def env_from_string(envname, config):
    # BSDDB requires that the directory already exists.  BAW: do we need to
    # adjust umask to ensure filesystem permissions?
    try:
        os.mkdir(envname)
    except OSError, e:
        if e.errno <> errno.EEXIST: raise
        # already exists
    # Create the lock file so no other process can open the environment.
    # This is required in order to work around the Berkeley lock
    # exhaustion problem (i.e. we do our own application level locks
    # rather than rely on Berkeley's finite page locks).
    lockpath = os.path.join(envname, '.lock')
    try:
        lockfile = open(lockpath, 'r+')
    except IOError, e:
        if e.errno <> errno.ENOENT: raise
        lockfile = open(lockpath, 'w+')
    lock_file(lockfile)
    lockfile.write(str(os.getpid()))
    lockfile.flush()
    try:
        # Create, initialize, and open the environment
        env = db.DBEnv()
        if config.logdir is not None:
            env.set_lg_dir(config.logdir)
        gbytes, bytes = divmod(config.cachesize, GBYTES)
        env.set_cachesize(gbytes, bytes)
        env.open(envname,
                 db.DB_CREATE          # create underlying files as necessary
                 | db.DB_RECOVER       # run normal recovery before opening
                 | db.DB_INIT_MPOOL    # initialize shared memory buffer pool
                 | db.DB_INIT_TXN      # initialize transaction subsystem
                 | db.DB_THREAD        # we use the env from multiple threads
                 )
    except:
        lockfile.close()
        raise
    return env, lockfile



class _WorkThread(threading.Thread):
    def __init__(self, storage, poll, checkinterval, name='work'):
        threading.Thread.__init__(self)
        self._storage = storage
        self._poll = poll
        self._interval = checkinterval
        self._name = name
        # Bookkeeping.  _nextcheck is useful as a non-public interface aiding
        # testing.  See test_autopack.py.
        self._stop = False
        self._nextcheck = checkinterval
        # We don't want these threads to hold up process exit.  That could
        # lead to corrupt databases, but recovery should ultimately save us.
        self.setDaemon(True)

    def run(self):
        name = self._name
        self._storage.log('%s thread started', name)
        while not self._stop:
            now = time.time()
            if now < self._nextcheck:
                continue
            self._storage.log('running %s', name)
            self._dowork()
            self._nextcheck = now + self._interval
            # Now we sleep for a little while before we check again.  We use a
            # poll timeout so that when the parent thread writes its "stop
            # marker" to the readfd, we'll exit out immediately.
            fds = self._poll.poll(self._interval * 1000)
            for fd, event in self._poll.poll(self._interval):
                # Just read and throw away the data.  The _stop flag will
                # already have been set if we're being shutdown.
                if event & select.POLLIN:
                    #print name, 'data:', os.read(fd, 1024)
                    os.read(fd, 1024)
        self._storage.log('%s thread finished', name)

    def stop(self):
        self._stop = True

    def _dowork(self):
        pass



class _Checkpoint(_WorkThread):
    def __init__(self, storage, poll, interval):
        _WorkThread.__init__(self, storage, poll, interval, 'checkpointing')

    def _dowork(self):
        self._storage.docheckpoint()
