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
#
#	Author: Sam Rushing <rushing@nightmare.com>
#

import exceptions
import select
import socket
import string
import sys

import os
if os.name == 'nt':
    EWOULDBLOCK = 10035
    EINPROGRESS = 10036
    EALREADY    = 10037
    ECONNRESET  = 10054
    ENOTCONN    = 10057
    ESHUTDOWN   = 10058
else:
    from errno import EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET, ENOTCONN, ESHUTDOWN

try:
    socket_map
except NameError:
    socket_map = {}

class ExitNow (exceptions.Exception):
    pass

DEBUG = 0

def poll (timeout=0.0, map=None):
    global DEBUG
    if map is None:
        map = socket_map
    if map:
        r = []; w = []; e = []
        for fd, obj in map.items():
            if obj.readable():
                r.append (fd)
            if obj.writable():
                w.append (fd)
        r,w,e = select.select (r,w,e, timeout)

        if DEBUG:
            print r,w,e

        for fd in r:
            try:
                obj = map[fd]
                try:
                    obj.handle_read_event()
                except ExitNow:
                    raise ExitNow
                except:
                    obj.handle_error()
            except KeyError:
                pass

        for fd in w:
            try:
                obj = map[fd]
                try:
                    obj.handle_write_event()
                except ExitNow:
                    raise ExitNow
                except:
                    obj.handle_error()
            except KeyError:
                pass

def poll2 (timeout=0.0, map=None):
    import poll
    if map is None:
        map=socket_map
    # timeout is in milliseconds
    timeout = int(timeout*1000)
    if map:
        l = []
        for fd, obj in map.items():
            flags = 0
            if obj.readable():
                flags = poll.POLLIN
            if obj.writable():
                flags = flags | poll.POLLOUT
            if flags:
                l.append ((fd, flags))
        r = poll.poll (l, timeout)
        for fd, flags in r:
            try:
                obj = map[fd]
                try:
                    if (flags  & poll.POLLIN):
                        obj.handle_read_event()
                    if (flags & poll.POLLOUT):
                        obj.handle_write_event()
                except ExitNow:
                    raise ExitNow
                except:
                    obj.handle_error()
            except KeyError:
                pass

def loop (timeout=30.0, use_poll=0, map=None):

    if use_poll:
        poll_fun = poll2
    else:
        poll_fun = poll

        if map is None:
            map=socket_map

    while map:
        poll_fun (timeout, map)

class dispatcher:
    debug = 0
    connected = 0
    accepting = 0
    closing = 0
    addr = None

    def __init__ (self, sock=None, map=None):
        if sock:
            self.set_socket (sock, map)
            # I think it should inherit this anyway
            self.socket.setblocking (0)
            self.connected = 1

    def __repr__ (self):
        try:
            status = []
            if self.accepting and self.addr:
                status.append ('listening')
            elif self.connected:
                status.append ('connected')
            if self.addr:
                status.append ('%s:%d' % self.addr)
            return '<%s %s at %x>' % (
                self.__class__.__name__,
                string.join (status, ' '),
                id(self)
                )
        except:
            try:
                ar = repr(self.addr)
            except:
                ar = 'no self.addr!'
                
            return '<__repr__ (self) failed for object at %x (addr=%s)>' % (id(self),ar)

    def add_channel (self, map=None):
        #self.log_info ('adding channel %s' % self)
        if map is None:
            map=socket_map
        map [self._fileno] = self

    def del_channel (self, map=None):
        fd = self._fileno
        if map is None:
            map=socket_map
        if map.has_key (fd):
            #self.log_info ('closing channel %d:%s' % (fd, self))
            del map [fd]

    def create_socket (self, family, type):
        self.family_and_type = family, type
        self.socket = socket.socket (family, type)
        self.socket.setblocking(0)
        self._fileno = self.socket.fileno()
        self.add_channel()

    def set_socket (self, sock, map=None):
        self.__dict__['socket'] = sock
        self._fileno = sock.fileno()
        self.add_channel (map)

    def set_reuse_addr (self):
        # try to re-use a server port if possible
        try:
            self.socket.setsockopt (
                socket.SOL_SOCKET, socket.SO_REUSEADDR,
                self.socket.getsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR) | 1
                )
        except:
            pass

    # ==================================================
    # predicates for select()
    # these are used as filters for the lists of sockets
    # to pass to select().
    # ==================================================

    def readable (self):
        return 1

    if os.name == 'mac':
        # The macintosh will select a listening socket for
        # write if you let it.  What might this mean?
        def writable (self):
            return not self.accepting
    else:
        def writable (self):
            return 1

    # ==================================================
    # socket object methods.
    # ==================================================

    def listen (self, num):
        self.accepting = 1
        if os.name == 'nt' and num > 5:
            num = 1
        return self.socket.listen (num)

    def bind (self, addr):
        self.addr = addr
        return self.socket.bind (addr)

    def connect (self, address):
        self.connected = 0
        try:
            self.socket.connect (address)
        except socket.error, why:
            if why[0] in (EINPROGRESS, EALREADY, EWOULDBLOCK):
                return
            else:
                raise socket.error, why
        self.connected = 1
        self.handle_connect()

    def accept (self):
        try:
            conn, addr = self.socket.accept()
            return conn, addr
        except socket.error, why:
            if why[0] == EWOULDBLOCK:
                pass
            else:
                raise socket.error, why

    def send (self, data):
        try:
            result = self.socket.send (data)
            return result
        except socket.error, why:
            if why[0] == EWOULDBLOCK:
                return 0
            else:
                raise socket.error, why
            return 0

    def recv (self, buffer_size):
        try:
            data = self.socket.recv (buffer_size)
            if not data:
                # a closed connection is indicated by signaling
                # a read condition, and having recv() return 0.
                self.handle_close()
                return ''
            else:
                return data
        except socket.error, why:
            # winsock sometimes throws ENOTCONN
            if why[0] in [ECONNRESET, ENOTCONN, ESHUTDOWN]:
                self.handle_close()
                return ''
            else:
                raise socket.error, why

    def close (self):
        self.del_channel()
        self.socket.close()

    # cheap inheritance, used to pass all other attribute
    # references to the underlying socket object.
    def __getattr__ (self, attr):
        return getattr (self.socket, attr)

    # log and log_info maybe overriden to provide more sophisitcated
    # logging and warning methods. In general, log is for 'hit' logging
    # and 'log_info' is for informational, warning and error logging. 

    def log (self, message):
        sys.stderr.write ('log: %s\n' % str(message))

    def log_info (self, message, type='info'):
        if __debug__ or type != 'info':
            print '%s: %s' % (type, message)

    def handle_read_event (self):
        if self.accepting:
            # for an accepting socket, getting a read implies
            # that we are connected
            if not self.connected:
                self.connected = 1
            self.handle_accept()
        elif not self.connected:
            self.handle_connect()
            self.connected = 1
            self.handle_read()
        else:
            self.handle_read()

    def handle_write_event (self):
        # getting a write implies that we are connected
        if not self.connected:
            self.handle_connect()
            self.connected = 1
        self.handle_write()

    def handle_expt_event (self):
        self.handle_expt()

    def handle_error (self):
        (file,fun,line), t, v, tbinfo = compact_traceback()

        # sometimes a user repr method will crash.
        try:
            self_repr = repr (self)
        except:
            self_repr = '<__repr__ (self) failed for object at %0x>' % id(self)

        self.log_info (
            'uncaptured python exception, closing channel %s (%s:%s %s)' % (
                self_repr,
                t,
                v,
                tbinfo
                ),
            'error'
            )
        self.close()

    def handle_expt (self):
        self.log_info ('unhandled exception', 'warning')

    def handle_read (self):
        self.log_info ('unhandled read event', 'warning')

    def handle_write (self):
        self.log_info ('unhandled write event', 'warning')

    def handle_connect (self):
        self.log_info ('unhandled connect event', 'warning')

    def handle_accept (self):
        self.log_info ('unhandled accept event', 'warning')

    def handle_close (self):
        self.log_info ('unhandled close event', 'warning')
        self.close()

# ---------------------------------------------------------------------------
# adds simple buffered output capability, useful for simple clients.
# [for more sophisticated usage use asynchat.async_chat]
# ---------------------------------------------------------------------------

class dispatcher_with_send (dispatcher):
    def __init__ (self, sock=None):
        dispatcher.__init__ (self, sock)
        self.out_buffer = ''

    def initiate_send (self):
        num_sent = 0
        num_sent = dispatcher.send (self, self.out_buffer[:512])
        self.out_buffer = self.out_buffer[num_sent:]

    def handle_write (self):
        self.initiate_send()

    def writable (self):
        return (not self.connected) or len(self.out_buffer)

    def send (self, data):
        if self.debug:
            self.log_info ('sending %s' % repr(data))
        self.out_buffer = self.out_buffer + data
        self.initiate_send()

# ---------------------------------------------------------------------------
# used for debugging.
# ---------------------------------------------------------------------------

def compact_traceback ():
    t,v,tb = sys.exc_info()
    tbinfo = []
    while 1:
        tbinfo.append ((
            tb.tb_frame.f_code.co_filename,
            tb.tb_frame.f_code.co_name,             
            str(tb.tb_lineno)
            ))
        tb = tb.tb_next
        if not tb:
            break

    # just to be safe
    del tb

    file, function, line = tbinfo[-1]
    info = '[' + string.join (
        map (
            lambda x: string.join (x, '|'),
            tbinfo
            ),
        '] ['
        ) + ']'
    return (file, function, line), t, v, info

def close_all (map=None):
    if map is None:
        map=socket_map
    for x in map.values():
        x.socket.close()
    map.clear()

# Asynchronous File I/O:
#
# After a little research (reading man pages on various unixen, and
# digging through the linux kernel), I've determined that select()
# isn't meant for doing doing asynchronous file i/o.
# Heartening, though - reading linux/mm/filemap.c shows that linux
# supports asynchronous read-ahead.  So _MOST_ of the time, the data
# will be sitting in memory for us already when we go to read it.
#
# What other OS's (besides NT) support async file i/o?  [VMS?]
#
# Regardless, this is useful for pipes, and stdin/stdout...

import os
if os.name == 'posix':
    import fcntl
    import FCNTL

    class file_wrapper:
        # here we override just enough to make a file
        # look like a socket for the purposes of asyncore.
        def __init__ (self, fd):
            self.fd = fd

        def recv (self, *args):
            return apply (os.read, (self.fd,)+args)

        def write (self, *args):
            return apply (os.write, (self.fd,)+args)

        def close (self):
            return os.close (self.fd)

        def fileno (self):
            return self.fd

    class file_dispatcher (dispatcher):
        def __init__ (self, fd):
            dispatcher.__init__ (self)
            self.connected = 1
            # set it to non-blocking mode
            flags = fcntl.fcntl (fd, FCNTL.F_GETFL, 0)
            flags = flags | FCNTL.O_NONBLOCK
            fcntl.fcntl (fd, FCNTL.F_SETFL, flags)
            self.set_file (fd)

        def set_file (self, fd):
            self._fileno = fd
            self.socket = file_wrapper (fd)
            self.add_channel()

