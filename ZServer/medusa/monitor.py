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

#
# python REPL channel.
#

RCS_ID = '$Id: monitor.py,v 1.7 2000/05/31 20:53:13 brian Exp $'

import md5
import socket
import string
import sys
import time

VERSION = string.split(RCS_ID)[2]

import asyncore
import asynchat

from counter import counter
import producers

class monitor_channel (asynchat.async_chat):
	try_linemode = 1

	def __init__ (self, server, sock, addr):
		asynchat.async_chat.__init__ (self, sock)
		self.server = server
		self.addr = addr
		self.set_terminator ('\r\n')
		self.data = ''
		# local bindings specific to this channel
		self.local_env = sys.modules['__main__'].__dict__.copy()
		self.push ('Python ' + sys.version + '\r\n')
		self.push (sys.copyright+'\r\n')
		self.push ('Welcome to %s\r\n' % self)
		self.push ("[Hint: try 'from __main__ import *']\r\n")
		self.prompt()
		self.number = server.total_sessions.as_long()
		self.line_counter = counter()
		self.multi_line = []
		
	def handle_connect (self):
		# send IAC DO LINEMODE
		self.push ('\377\375\"')

	def close (self):
		self.server.closed_sessions.increment()
		asynchat.async_chat.close(self)

	def prompt (self):
		self.push ('>>> ')

	def collect_incoming_data (self, data):
		self.data = self.data + data
		if len(self.data) > 1024:
			# denial of service.
			self.push ('BCNU\r\n')
			self.close_when_done()

	def found_terminator (self):
		line = self.clean_line (self.data)
		self.data = ''
		self.line_counter.increment()
		# check for special case inputs...
		if not line and not self.multi_line:
			self.prompt()
			return
		if line in ['\004', 'exit']:
			self.push ('BCNU\r\n')
			self.close_when_done()
			return
		oldout = sys.stdout
		olderr = sys.stderr
		try:
			p = output_producer(self, olderr)
			sys.stdout = p
			sys.stderr = p
			try:
				# this is, of course, a blocking operation.
				# if you wanted to thread this, you would have
				# to synchronize, etc... and treat the output
				# like a pipe.  Not Fun.
				#
				# try eval first.  If that fails, try exec.  If that fails,
				# hurl.
				try:
					if self.multi_line:
						# oh, this is horrible...
						raise SyntaxError
					co = compile (line, repr(self), 'eval')
					result = eval (co, self.local_env)
					method = 'eval'
					if result is not None:
						print repr(result)
					self.local_env['_'] = result
				except SyntaxError:
					try:
						if self.multi_line:
							if line and line[0] in [' ','\t']:
								self.multi_line.append (line)
								self.push ('... ')
								return
							else:
								self.multi_line.append (line)
								line =	string.join (self.multi_line, '\n')
								co = compile (line, repr(self), 'exec')
								self.multi_line = []
						else:
							co = compile (line, repr(self), 'exec')
					except SyntaxError, why:
						if why[0] == 'unexpected EOF while parsing':
							self.push ('... ')
							self.multi_line.append (line)
							return
					exec co in self.local_env
					method = 'exec'
			except:
				method = 'exception'
				self.multi_line = []
				(file, fun, line), t, v, tbinfo = asyncore.compact_traceback()
				self.log_info('%s %s %s' %(t, v, tbinfo), 'warning')
		finally:
			sys.stdout = oldout
			sys.stderr = olderr
		self.log_info('%s:%s (%s)> %s' % (
			self.number,
			self.line_counter,
			method,
			repr(line))
			)
		self.push_with_producer (p)
		self.prompt()
		
	# for now, we ignore any telnet option stuff sent to
	# us, and we process the backspace key ourselves.
	# gee, it would be fun to write a full-blown line-editing
	# environment, etc...
	def clean_line (self, line):
		chars = []
		for ch in line:
			oc = ord(ch)
			if oc < 127:
				if oc in [8,177]:
					# backspace
					chars = chars[:-1]
				else:
					chars.append (ch)
		return string.join (chars, '')

class monitor_server (asyncore.dispatcher):

	SERVER_IDENT = 'Monitor Server (V%s)' % VERSION

	channel_class = monitor_channel

	def __init__ (self, hostname='127.0.0.1', port=8023):
		self.hostname = hostname
		self.port = port
		self.create_socket (socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind ((hostname, port))
		self.log_info('%s started on port %d' % (self.SERVER_IDENT, port))
		self.listen (5)
		self.closed		= 0
		self.failed_auths = 0
		self.total_sessions = counter()
		self.closed_sessions = counter()

	def writable (self):
		return 0

	def handle_accept (self):
		conn, addr = self.accept()
		self.log_info('Incoming monitor connection from %s:%d' % addr)
		self.channel_class (self, conn, addr)
		self.total_sessions.increment()

	def status (self):
		return producers.simple_producer (
			'<h2>%s</h2>'						% self.SERVER_IDENT
			+ '<br><b>Total Sessions:</b> %s'		% self.total_sessions
			+ '<br><b>Current Sessions:</b> %d'	% (
				self.total_sessions.as_long()-self.closed_sessions.as_long()
				)
			)

def hex_digest (s):
	m = md5.md5()
	m.update (s)
	return string.joinfields (
		map (lambda x: hex (ord (x))[2:], map (None, m.digest())),
		'',
		)

class secure_monitor_channel (monitor_channel):
	authorized = 0
	
	def __init__ (self, server, sock, addr):
		asynchat.async_chat.__init__ (self, sock)
		self.server = server
		self.addr = addr
		self.set_terminator ('\r\n')
		self.data = ''
		# local bindings specific to this channel
		self.local_env = {}
		# send timestamp string
		self.timestamp = str(time.time())
		self.count = 0
		self.line_counter = counter()
		self.number = int(server.total_sessions.as_long())
		self.multi_line = []
		self.push (self.timestamp + '\r\n')

	def found_terminator (self):
		if not self.authorized:
			if hex_digest ('%s%s' % (self.timestamp, self.server.password)) != self.data:
				self.log_info ('%s: failed authorization' % self, 'warning')
				self.server.failed_auths = self.server.failed_auths + 1
				self.close()
			else:
				self.authorized = 1
				self.push ('Python ' + sys.version + '\r\n')
				self.push (sys.copyright+'\r\n')
				self.push ('Welcome to %s\r\n' % self)
				self.prompt()
				self.data = ''
		else:
			monitor_channel.found_terminator (self)
		
class secure_encrypted_monitor_channel (secure_monitor_channel):
	"Wrap send() and recv() with a stream cipher"

	def __init__ (self, server, conn, addr):
		key = server.password
		self.outgoing = server.cipher.new (key)
		self.incoming = server.cipher.new (key)
		secure_monitor_channel.__init__ (self, server, conn, addr)

	def send (self, data):
		# send the encrypted data instead
		ed = self.outgoing.encrypt (data)
		return secure_monitor_channel.send (self, ed)

	def recv (self, block_size):
		data = secure_monitor_channel.recv (self, block_size)
		if data:
			dd = self.incoming.decrypt (data)
			return dd
		else:
			return data

class secure_monitor_server (monitor_server):
	channel_class = secure_monitor_channel

	def __init__ (self, password, hostname='', port=8023):
		monitor_server.__init__ (self, hostname, port)
		self.password = password

	def status (self):
		p = monitor_server.status (self)
		# kludge
		p.data = p.data + ('<br><b>Failed Authorizations:</b> %d' % self.failed_auths)
		return p

# don't try to print from within any of the methods
# of this object. 8^)

class output_producer:
	def __init__ (self, channel, real_stderr):
		self.channel = channel
		self.data = ''
		# use _this_ for debug output
		self.stderr = real_stderr

	def check_data (self):
		if len(self.data) > 1<<16:
			# runaway output, close it.
			self.channel.close()
			
	def write (self, data):
		lines = string.splitfields (data, '\n')
		data = string.join (lines, '\r\n')
		self.data = self.data + data
		self.check_data()
		
	def writeline (self, line):
		self.data = self.data + line + '\r\n'
		self.check_data()
		
	def writelines (self, lines):
		self.data = self.data + string.joinfields (
			lines,
			'\r\n'
			) + '\r\n'
		self.check_data()

	def ready (self):
		return (len (self.data) > 0)

	def flush (self):
		pass

	def softspace (self, *args):
		pass

	def more (self):
		if self.data:
			result = self.data[:512]
			self.data = self.data[512:]
			return result
		else:
			return ''

if __name__ == '__main__':
	import string
	import sys
	if '-s' in sys.argv:
		sys.argv.remove ('-s')
		print 'Enter password: ',
		password = raw_input()
	else:
		password = None

	if '-e' in sys.argv:
		sys.argv.remove ('-e')
		encrypt = 1
	else:
		encrypt = 0

	print sys.argv
	if len(sys.argv) > 1:
		port = string.atoi (sys.argv[1])
	else:
		port = 8023

	if password is not None:
		s = secure_monitor_server (password, '', port)
		if encrypt:
			s.channel_class = secure_encrypted_monitor_channel
			import sapphire
			s.cipher = sapphire
	else:
		s = monitor_server ('', port)
	asyncore.loop()
