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

# CommitLog class
#
# This class implements the action log for writes to non-committed
# transactions.  They are replayed and applied all at once during _finish()
# which is called by BaseStorage's tpc_finish().  See FullImplementation.txt
# and notes for some discussion of the issues involved.
#
# BAW: understand this more, and figure out why we can't use BSDDB's
# lock_detect().
#
# File format:
#
# The log file consists of a standard header, followed by a number of marshal
# records.  Each marshal consists of a single character opcode and an
# argument.  The specific opcodes and arguments depend on the type of storage
# using the CommitLog instance, and derived classes provide a more specific
# interface for the storage.

__version__ = '$Revision: 1.10 $'.split()[-2:][0]

import sha
import struct
import os
import time
import marshal
import errno
from types import StringType

# JF: POSError is the ZODB version of Exception; it's fairly generic
# so a more specific exception might be better.  E.g. StorageError
from ZODB.POSException import POSError

# Log file states.
#
# START is the transaction start state, and the log file must either not exist
# or be in the COMMITTED state in order to enter the START state.
START = 'S'

# OPEN state is where objects have begun to be stored into the log file during
# an open transaction.  OPEN can only be entered from the START state, and
# upon the first object store, the state goes from START->OPEN.  From here the
# transaction will either be committed or aborted.
OPEN = 'O'

# If the transaction is aborted, everything is discarded and the commit log is
# moved to the START state.  This can only happen from the START or OPEN
# state.  If the transaction is finished, then we are guaranteeing that the
# stored objects will be saved to the back-end storage.  In that case we
# change the state to PROMISED and allow the storage to read the objects out
# again.
#
# Once the transaction commit has succeeded, the file's state is moved back to
# START for the next transaction.
PROMISED = 'P'

# Magic number for log file header
MAGIC = 0xfeedb00bL
# Version number
SCHEMA = 0x01
# The format of the file header.  It consists of:
#   - a 32 bit magic number
#   - the 16-bit schema number
#   - the single character commit log state flag
FMT = '>IHc'
FMTSZ = struct.calcsize(FMT)



class CommitLogError(POSError):
    """Base class for errors raised by the CommitLog class."""

class TruncationError(CommitLogError):
    """A log file truncation was detected on a header read."""

class LogCorruptedError(CommitLogError):
    """A read of a data record was incomplete or corrupted."""

class StateTransitionError(CommitLogError):
    """An illegal state transition was attempted."""
    def __init__(self, state):
        self.__state = state

    def __str__(self):
        return 'at invalid state: %c' % self.__state

class UncommittedChangesError(StateTransitionError):
    """The commit log has uncommitted changes.

    This exception indicates that a promised commit of object states was not
    either aborted or finished committing.  No further object updates will be
    allowed until the log file is replayed and explicitly cleared.
    """



class CommitLog:
    def __init__(self, file=None, dir='.'):
        """Initialize the commit log, usually with a new file.

        This is not a real temporary file because if we crash before the
        transaction is committed, we'll need to replay this log.  However, we
        also need to be especially careful about the mode this file is written
        in, otherwise evil processes could snoop information.

        If `file' is provided it must be an already open file-like object that
        supports seek() and appending r/w in binary mode.

        Or `file' can be the name of a file which will be created with those
        semantics.  If `file' is omitted, we create a new such file, from a
        (hopefully uniquely) crafted filename.  In either of these two cases,
        the filename is relative to dir (the default is the current
        directory).

        The commit file has a header consisting of the following information:

        - a 32 bit magic number
        - the 16-bit schema number
        - the single character commit log state flag

        Integers are standard size, big-endian.

        """

        # BAW: is our filename unique enough?  Are we opening it up with too
        # much or too little security?
        self._unlink = 1
        self._fp = None
        if file is None:
            # Create the file from scratch.  We know the file has to be in the
            # init state, so just go ahead and write the appropriate header.
            now = time.time()
            pid = os.getpid()
            file = sha.new(`now` + `pid`).hexdigest()
            # BAW: what directory to create this in?  /tmp doesn't seem right.
            omask = os.umask(077)                 # -rw-------
            try:
                try:
                    os.makedirs(dir)
                except OSError, e:
                    if e.errno <> errno.EEXIST: raise
                self._fp = open(os.path.join(dir, file), 'w+b')
            finally:
                os.umask(omask)
            self._writehead(START)
        elif isinstance(file, StringType):
            # Open the file in the proper mode.  If it doesn't exist, write
            # the start header.
            omask = os.umask(077)
            try:
                try:
                    os.makedirs(dir)
                except OSError, e:
                    if e.errno <> errno.EEXIST: raise
                self._fp = open(os.path.join(dir, file), 'w+b')
            finally:
                os.umask(omask)
            # Attempt to read any existing header.  If we get an error, assume
            # the file was created from scratch and write the start header.
            try:
                self._readhead()
            except TruncationError:
                self._writehead(START)
        else:
            # File object was created externally; maybe we're replaying an old
            # log.  Read the file's header and initialize our state from it.
            self._fp = file
            self._readhead()
            self._unlink = 0

    def get_filename(self):
        return self._fp.name

    def _writehead(self, state, pack=struct.pack):
        # Scribble a new header onto the front of the file.  state is the
        # 1-character state flag.
        assert len(state) == 1
        self._state = state
        data = pack(FMT, MAGIC, SCHEMA, state)
        pos = self._fp.tell()
        self._fp.seek(0)
        self._fp.write(data)
        self._fp.flush()
        # Seek to the old file position, or just past the header, whichever is
        # farther away.
        self._fp.seek(max(self._fp.tell(), pos))

    def _readhead(self, unpack=struct.unpack):
        # Read the current file header, and return a tuple of the header data.
        # If the file for some reason doesn't contain a complete header, a
        # TruncationError is raised.
        pos = self._fp.tell()
        self._fp.seek(0)
        header = self._fp.read(FMTSZ)
        if len(header) <> FMTSZ:
            raise TruncationError('short header read: %d bytes' % len(header))
        try:
            magic, schema, state = unpack(FMT, header)
        except struct.error, e:
            raise LogCorruptedError, e
        if magic <> MAGIC:
            raise LogCorruptedError, 'bad magic number: %x' % magic
        #
        # for now there's no backwards compatibility necessary
        if schema <> SCHEMA:
            raise LogCorruptedError, 'bad version number: %d' % schema
        self._state = state
        # See to the old file position, or just past the header, whichever is
        # farther away.
        self._fp.seek(max(self._fp.tell(), pos))

    def _append(self, key, record, dump=marshal.dump):
        # Store the next record in the file.  Key is a single character
        # marking the record type.  Record must be a tuple of some record-type
        # specific data.  Record types and higher level write methods are
        # defined in derived classes.
        assert len(key) == 1
        # Make assertions about the file's state
        assert self._state in (START, OPEN, PROMISED)
        if self._state == START:
            self._writehead(OPEN)
        elif self._state == OPEN:
            pass
        elif self._state == PROMISED:
            raise UncommittedChangesError(
                'Cannot write while promised updates remain uncommitted')
        # We're good to go, append the object
        self._fp.seek(0, 2)                       # to end of file
        if self._fp.tell() < FMTSZ:
            raise TruncationError, 'Last seek position < end of headers'
        dump((key, record), self._fp)
        self._fp.flush()

    def start(self, load=marshal.load):
        """Move the file pointer to the start of the record data."""
        self._readhead()
        if self._state <> START:
            raise StateTransitionError, self._state
        self._fp.seek(FMTSZ)

    def promise(self):
        """Move the transition to the PROMISED state, where we guarantee that
        any changes to the object state will be committed to the backend
        database before we ever write more updates.
        """
        if self._state not in (START, OPEN):
            raise StateTransitionError, self._state
        self._writehead(PROMISED)
        self._fp.seek(FMTSZ)

    def finish(self):
        """We've finished committing all object updates to the backend
        storage, or we're aborting the transation.  In either case, we're done
        with the data in our log file.  Move the transition back to the start
        state.
        """
        # We need to truncate the file after writing the header, for the
        # algorithm above to work.
        self._writehead(START)
        self._fp.truncate()

    def _next(self, load=marshal.load):
        # Read the next marshal record from the log.  If there is no next
        # record return None, otherwise return a 2-tuple of the record type
        # character and the data tuple.
        try:
            return load(self._fp)
        except EOFError:
            return None
        # BAW: let TypeError percolate up.

    def next(self):
        raise NotImplementedError

    def close(self, unlink=1):
        """Close the file.

        If unlink is true, delete the underlying file object too.
        """
        if self._fp:
            self._fp.close()
            if (unlink or self._unlink) and os.path.exists(self._fp.name):
                os.unlink(self._fp.name)
                self._fp = None

    def __del__(self):
        # Unsafe, and file preserving close
        self.close()



class PacklessLog(CommitLog):
    # Higher level interface for reading and writing version-less/undo-less
    # log records.
    #
    # Record types:
    #     'o' - object state, consisting of an oid, and the object's pickle
    #           data
    #
    def write_object(self, oid, pickle):
        self._append('o', (oid, pickle))

    def next(self):
        # Get the next object pickle data.  Return the oid and the pickle
        # string.  Raise a LogCorruptedError if there's an incomplete marshal
        # record.
        rec = self._next()
        if rec is None:
            return None
        try:
            key, (oid, pickle) = rec
        except ValueError:
            raise LogCorruptedError, 'incomplete record'
        if key <> 'o':
            raise LogCorruptedError, 'bad record key: %s' % key
        return oid, pickle



class FullLog(CommitLog):
    # Higher level interface for reading and writing full versioning and
    # undoable log records.
    #
    # Record types:
    #     'o' - object state, consisting of an oid, vid, non-version revision
    #           id (nvrevid), live revision id (lrevid), the object's pickle,
    #           and a previous revision id (prevrevid).  Note that there are
    #           actually higher level API method that write essentially the
    #           same record with some of the elements defaulted to the empty
    #           string or the "all-zeros" string.
    #     'v' - new version record, consisting of a version string and a
    #           version id
    #     'd' - discard version, consisting of a version id
    #
    def __init__(self, file=None, dir='.'):
        """Initialize the `full' commit log, usually with a new file."""
        CommitLog.__init__(self, file, dir)
        self.__versions = {}
        self.__prevrevids = {}

    def finish(self):
        CommitLog.finish(self)
        self.__versions.clear()
        self.__prevrevids.clear()

    def get_vid(self, version, missing=None):
        """Given a version string, return the associated vid.
        If not present, return `missing'.
        """
        return self.__versions.get(version, missing)

    def get_prevrevid(self, oid, missing=None):
        """Given an object id, return the associated prevrevid.
        If not present, return `missing'.

        This method serves to allow transactionalUndo() to find undone
        transactions that have been committed to the log, but not to the
        database (i.e. multiple transactionalUndo()'s during a single
        transaction).
        """
        return self.__prevrevids.get(oid, missing)

    # read/write protocol

    def write_object(self, oid, vid, nvrevid, pickle, prevrevid):
        # Write an empty lrevid since that will be the same as the transaction
        # id at the time of the commit to Berkeley.
        self._append('o', (oid, vid, nvrevid, '', pickle, prevrevid))

    def write_nonversion_object(self, oid, lrevid, prevrevid, zero='\0'*8):
        # Write zeros for the vid and nvrevid since we're storing this object
        # into version zero (the non-version).  Also, write an empty pickle
        # since we'll reuse one already in the pickle table.
        self._append('o', (oid, zero, zero, lrevid, '', prevrevid))

    def write_moved_object(self, oid, vid, nvrevid, lrevid, prevrevid):
        # Write an empty pickle since we're just moving the object and we'll
        # reuse the pickle already in the database.
        self._append('o', (oid, vid, nvrevid, lrevid, '', prevrevid))

    def write_object_undo(self, oid, vid, nvrevid, lrevid, prevrevid):
        # Identical to write_moved_object() except that we have to keep some
        # extra info around.  Specifically, it's possible to undo multiple
        # transactions in the same transaction.
        self._append('o', (oid, vid, nvrevid, lrevid, '', prevrevid))
        self.__prevrevids[oid] = prevrevid

    def write_new_version(self, version, vid):
        self._append('v', (version, vid))

    def write_discard_version(self, vid):
        self._append('d', (vid,))

    def next(self):
        # Get the next object record.  Return the key for unpacking and the
        # object record data.
        rec = self._next()
        if rec is None:
            return None
        try:
            key, data = rec
        except ValueError:
            raise LogCorruptedError, 'incomplete record'
        if key not in 'ovd':
            raise LogCorruptedError, 'bad record key: %s' % key
        return key, data
