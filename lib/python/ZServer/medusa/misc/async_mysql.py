# -*- Mode: Python; tab-width: 4 -*-

VERSION_STRING = '$Id: async_mysql.py,v 1.3 2001/05/01 11:45:26 andreas Exp $'

import exceptions
import math
import socket
import string
import sys

import asyncore
import asynchat

from continuation import continuation
from fifo import fifo

class mysql_error (exceptions.Exception):
    pass
    
    # ===========================================================================
    #						   Authentication
    # ===========================================================================
    
    # Note: I've ignored the stuff to support an older version of the protocol.
    #
    # The code is based on the file mysql-3.21.33/client/password.c
    #
    # The auth scheme is challenge/response.  Upon connection the server
    # sends an 8-byte challenge message.  This is hashed with the password
    # to produce an 8-byte response.  The server side performs an identical
    # hash to verify the password is correct.
    
class random_state:

    def __init__ (self, seed, seed2):
        self.max_value = 0x3FFFFFFF
        self.seed = seed % self.max_value
        self.seed2 = seed2 % self.max_value
        
    def rnd (self):
        self.seed = (self.seed * 3 + self.seed2) % self.max_value
        self.seed2 = (self.seed + self.seed2 + 33) % self.max_value
        return float(self.seed)/ float(self.max_value)
        
def hash_password (password):
    nr=1345345333L
    add=7
    nr2=0x12345671L
    for ch in password:
        if (ch == ' ') or (ch == '\t'):
            continue
        tmp = ord(ch)
        nr = nr ^ (((nr & 63) + add) * tmp) + (nr << 8)
        nr2 = nr2 + ((nr2 << 8) ^ nr)
        add = add + tmp
    return (
            nr & ((1L<<31)-1L),
            nr2 & ((1L<<31)-1L)
            )
    
def scramble (message, password):
    hash_pass = hash_password (password)
    hash_mess = hash_password (message)
    r = random_state (
            hash_pass[0] ^ hash_mess[0],
            hash_pass[1] ^ hash_mess[1]
            )
    to = []
    for ch in message:
        to.append (int (math.floor ((r.rnd() * 31) + 64)))
    extra = int (math.floor (r.rnd()*31))
    for i in range(len(to)):
        to[i] = to[i] ^ extra
    return to
    
    # ===========================================================================
    #						   Packet Protocol
    # ===========================================================================
    
def unpacket (p):
        # 3-byte length, one-byte packet number, followed by packet data
    a,b,c,s = map (ord, p[:4])
    l = a | (b << 8) | (c << 16)
    # s is a sequence number
    return l, s
    
def packet (data, s=0):
    l = len(data)
    a, b, c = l & 0xff, (l>>8) & 0xff, (l>>16) & 0xff
    h = map (chr, [a,b,c,s])
    return string.join (h,'') + data
    
def n_byte_num (data, n):
    result = 0
    for i in range(n):
        result = result | (ord(data[i])<<(8*i))
    return result
    
def net_field_length (data, pos=0):
    n = ord(data[pos])
    if n < 251:
        return n, 1
    elif n == 251:
        return None, 1
    elif n == 252:
        return n_byte_num (data, 2), 3
    elif n == 253:
        return n_byte_num (data, 3), 4
    else:
            # libmysql adds 6, why?
        return n_byte_num (data, 4), 5
        
        # used to generate the dumps below
def dump_hex (s):
    r1 = []
    r2 = []
    for ch in s:
        r1.append (' %02x' % ord(ch))
        if (ch in string.letters) or (ch in string.digits):
            r2.append ('  %c' % ch)
        else:
            r2.append ('   ')
    return string.join (r1, ''), string.join (r2, '')
    
    # ===========================================================================
    #							 MySQL Client
    # ===========================================================================
    
class mysql_client (asynchat.async_chat):

        # protocol state
    PS_HEADER		= 1
    PS_DATA			= 2
    
    # auth state
    AS_LOGIN		= 1
    AS_CHALLENGE	= 2
    AS_RESPONSE		= 3
    
    def __init__ (self, username, password, login_callback, address=('127.0.0.1', 3306)):
        asynchat.async_chat.__init__ (self)
        self.username = username
        self.password = password
        self.server_address = address
        self.login (login_callback)
        self.current_database = None
        
    def login (self, callback):
        self.login_callback = callback
        self.buffer = ''
        self.set_terminator (None)
        address = self.server_address
        if type(address) == type(''):
            self.create_socket (socket.AF_UNIX, socket.SOCK_STREAM)
        else:
            self.create_socket (socket.AF_INET, socket.SOCK_STREAM)
        self._connected = 0
        self.connect (address)
        self.auth = self.AS_LOGIN
        self.state = self.PS_HEADER
        self.query_fifo = fifo()
        
    def handle_connect (self):
        self._connected = 1
        
    def close (self):
        asynchat.async_chat.close (self)
        self._connected = 0
        self.discard_buffers()
        # XXX: check query fifo for pending queries
        
    def collect_incoming_data (self, data):
            # packets come in with a four-byte head on them.
            # we need to stay sync'd with that.	 we use a
            # two-state machine.
        self.buffer = self.buffer + data
        while self.buffer:
            if self.state is self.PS_HEADER:
                    # do we have a complete header?
                if len(self.buffer) >= 4:
                    l,s = unpacket (self.buffer)
                    self.pinfo = l, s
                    self.state = self.PS_DATA
                    self.buffer = self.buffer[4:]
                else:
                    break
            elif self.state is self.PS_DATA:
                l, s = self.pinfo
                if len(self.buffer) >= l:
                    data, self.buffer = self.buffer[:l], self.buffer[l:]
                    self.handle_packet (s, data)
                    self.state = self.PS_HEADER
                else:
                    break
                    
    def handle_packet (self, seq, data):
        if self.auth is self.AS_LOGIN:
                # unpack the greeting
            protocol_version = ord(data[0])
            eos = string.find (data, '\000')
            mysql_version = data[1:eos]
            thread_id = n_byte_num (data[eos+1:eos+5], 4)
            challenge = data[eos+5:eos+13]
            self.auth = (
                    protocol_version,
                    mysql_version,
                    thread_id,
                    challenge
                    )
            # print auth
            lp = self.build_login_packet (challenge)
            # print 'login packet:',repr(lp)
            self.auth = self.AS_CHALLENGE
            # seems to require a sequence number of one
            self.push (packet (lp, 1))
        elif self.auth is self.AS_CHALLENGE:
            if seq != 2:
                self.login_callback (self, 0)
            else:
                self.auth = self.AS_RESPONSE
                self.login_callback (self, 1)
        else:
            if seq == 1:
                callback = self.query_fifo.pop()
                if callback:
                    self.current_callback = callback
                    callback (seq, data)
            else:
                if self.current_callback:
                    self.current_callback (seq, data)
                    
    def build_login_packet (self, challenge):
        auth = string.join (map (chr, scramble (challenge, self.password)), '')
        # 2 bytes of client_capability
        # 3 bytes of max_allowed_packet
        # no idea what they are
        return '\005\000\000\000\020' + self.username + '\000' + auth
        
    def push_query (self, query, callback=None, sequence=0):
        if self._connected:
            self.push (packet (query, sequence))
            self.query_fifo.push (callback)
        else:
            self.login (
                    continuation (self._relogin, (query, callback, sequence))
                    )
            
            # ======================================================================
            #					auto-reconnect support
            # ======================================================================
            
    def _relogin (self, (query, callback, sequence), ignore, result):
        if result:
            if self.current_database:
                self.cmd_use (
                        self.current_database,
                        continuation (self._relogin_use, (query, callback, sequence))
                        )
            else:
                self.push_query (query, callback, sequence)
        else:
                # XXX all callbacks need an 'error' parameter.
            raise SystemError, "Couldn't reconnect to mysql server"
            
    def _relogin_use (self, (query, callback, sequence), nfields, data):
            # this should really be done by cmd_use... (i.e., use a continuation object)
        if (nfields > 0) and (data == '\000\000\000'):
            self.push_query (query, callback, sequence)
        else:
                # XXX all callbacks need an 'error' parameter.
            raise SystemError, "Couldn't reconnect to current database"
            
            # ======================================================================
            #						   Commands
            # ======================================================================
            
            # from mysql-3.21.33/include/mysql_com.h.in
            #
            
    cmds = [
            'sleep', 'quit', 'init_db', 'query', 'field_list', 'create_db',
            'drop_db', 'refresh', 'shutdown', 'statistics', 'process_info',
            'connect', 'process_kill', 'debug'
            ]
    
    d = {}
    for i in range (len (cmds)):
        d[cmds[i]] = i
    cmds = d
    del d
    
    def command (self, command_type, command, callback):
        self.push_query (
                chr(self.cmds[command_type]) + command,
                callback
                )
        
    def cmd_use (self, database, callback=None):
        self.current_database = database
        self.command ('init_db', database, callback)
        
    def cmd_quit (self, callback=None):
        self.command ('quit', '', callback)
        
    def cmd_query (self, query, callback=None):
        self.command ('query', query, result_set (callback))
        
        # ===========================================================================
        #							  Result Set
        # ===========================================================================
        
class result_set:

    'unpack a result set'
    '  If <data_callback> is specified, it will be called'
    '  for each element of the result set.  Otherwise, the'
    '  results will be collected into a list made available'
    '  to <callback>'
    
    def __init__ (self, callback, data_callback=None):
        self.callback = callback
        self.packets = []
        self.nfields = None
        self.fields = []
        self.data = None
        self.data_callback = None
        
    def unpack_data (self, d):
        r = []
        i = 0
        while i < len(d):
            fl = ord(d[i])
            i = i + 1
            r.append (d[i:i+fl])
            i = i + fl
        return r
        
    def __call__ (self, seq, data):
        if self.nfields is None:
                # first packet is the number of fields (or an error)
            n = ord(data[0])
            if n == 0:
                self.callback ([], [])
            else:
                self.nfields = n
        elif self.data is None:
            if ord(data[0]) != 0xfe:
                    # collect field info
                self.fields.append (self.unpack_data (data))
            else:
                self.data = []
        else:
                # collect data
            if ord(data[0]) != 0xfe:
                if self.data_callback:
                    self.data_callback (self.unpack_data (data))
                else:
                    self.data.append (self.unpack_data (data))
            else:
                self.callback (self.fields, self.data)
                
if __name__ == '__main__':

    import random
    
    class test_mysql_client:
    
        def __init__ (self, client):
            self.client = client
            self.client.cmd_query ('create database test_async', self.callback_create)
            
        def callback_create (self, *info):
            print 'create database=>', info
            self.client.cmd_use ('test_async', self.callback_use)
            
        def callback_use (self, *info):
            print 'use=>', info
            self.client.cmd_query (
                    'create table users (name char(30), cool int)',
                    self.callback_create_table
                    )
            
        people = ['john', 'paul', 'george', 'ringo']
        
        def callback_create_table (self, *info):
            print 'create_table=>', info
            self.people_index = 0
            self.callback_insert ()
            
        def callback_insert (self, *info):
            print 'insert=>', info
            if self.people_index == len(self.people):
                self.client.cmd_query (
                        'select * from users',
                        self.callback_query
                        )
            else:
                self.client.cmd_query (
                        'insert into users values ("%s", %s)' % (
                                self.people[self.people_index],
                                random.randint (0,1)
                                ),
                        self.callback_insert
                        )
                self.people_index = self.people_index + 1
                
        def callback_query (self, fields, data):
            print 'query=>'
            print ' fields:'
            for field in fields:
                print '\t%s' % repr(field)
            print ' data:'
            for d in data:
                print '\t%s' % repr(d)
                
            self.client.command (
                    'drop_db',
                    'test_async',
                    self.callback_drop
                    )
            
        def callback_drop (self, *info):
            print 'drop=>', info
            self.client.cmd_quit (self.callback_quit)
            
        def callback_quit (self, *info):
            print 'quit=>', info
            
    def go (client, yesno):
        if yesno:
            test_mysql_client (client)
        else:
            print 'Failed to log in'
            
    import sys
    if len(sys.argv) < 4:
        print 'Usage: %s <username> <password> <host>' % sys.argv[0]
    else:
        [username, password, host]	= sys.argv[1:4]
        c = mysql_client (username, password, go, (host, 3306))
        asyncore.loop()
        
        # greeting:
        # * first byte is the protocol version (currently 10)
        # * null-terminated version string
        # * 4-byte thread id.
        # * 8-byte challenge
        # * 2-byte server capabilities?
        
        # message = [0x00, 0x39, 0x4d, 0x59, 0x59, 0x31, 0x29, 0x79, 0x47]
        # password = [0x66, 0x6e, 0x6f, 0x72, 0x64]
        
        # Handshake:
        #----------------------------------------
        #<== 000  0a 33 2e 32 32 2e 31 30 2d 62 65 74 61 00 1b 00 00 00 39 4d 59 59 31 29 79 47 00 0c 00
        #             3     2  2     1  0     b  e  t  a                 9  M  Y  Y  1     y  G         
        #----------------------------------------
        #==> 1
        #    05 00 00 00 10 72 75 73 68 69 6e 67 00 48 51 42 50 5d 4a 54 57
        #                    r  u  s  h  i  n  g     H  Q  B  P     J  T  W
        #----------------------------------------
        #<== 002  00 00 00
        
        # Insertion/Query (no result set)
        #----------------------------------------
        #==> 0
        #    03 69 6e 73 65 72 74 20 69 6e 74 6f 20 75 73 65 72 73 20 76 61 6c 75 65 73 20 28 22 61 73 64 66 40 61 73 64 66 2e 61 73 64 66 22 2c 20 22 6e 22 29
        #        i  n  s  e  r  t     i  n  t  o     u  s  e  r  s     v  a  l  u  e  s           a  s  d  f     a  s  d  f     a  s  d  f              n      
        #----------------------------------------
        #<== 001  00 01 00
        
        # Query (with result set)
        #----------------------------------------
        #==> 0
        #    03 73 65 6c 65 63 74 20 2a 20 66 72 6f 6d 20 75 73 65 72 73
        #        s  e  l  e  c  t           f  r  o  m     u  s  e  r  s
        #----------------------------------------
        #<== 001  02
        #           
        #<== 002  05 75 73 65 72 73 04 6e 61 6d 65 03 80 00 00 01 fe 03 00 00 00
        #             u  s  e  r  s     n  a  m  e                              
        #<== 003  05 75 73 65 72 73 0a 69 73 62 6f 75 6e 63 69 6e 67 03 01 00 00 01 fe 03 00 00 00
        #             u  s  e  r  s     i  s  b  o  u  n  c  i  n  g                              
        #<== 004  fe
        #           
        #<== 005  15 72 75 73 68 69 6e 67 40 6e 69 67 68 74 6d 61 72 65 2e 63 6f 6d 01 6e
        #             r  u  s  h  i  n  g     n  i  g  h  t  m  a  r  e     c  o  m     n
        #<== 006  0e 61 73 64 66 40 61 73 64 66 2e 61 73 64 66 01 6e
        #             a  s  d  f     a  s  d  f     a  s  d  f     n
        #<== 007  fe
        
        
        # "use bouncer_test"
        #==> 0
        #    02 62 6f 75 6e 63 65 72 5f 74 65 73 74
        #        b  o  u  n  c  e  r     t  e  s  t
        #----------------------------------------
        #<== 001  00 00 00
