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

# monitor client, unix version.

import asyncore
import asynchat
import regsub
import socket
import string
import sys
import os

import md5
import time

class stdin_channel (asyncore.file_dispatcher):
	def handle_read (self):
		data = self.recv(512)
		if not data:
			print '\nclosed.'
			self.sock_channel.close()
			try:
				self.close()
			except:
				pass
			
		data = regsub.gsub ('\n', '\r\n', data)
		self.sock_channel.push (data)

	def writable (self):
		return 0

	def log (self, *ignore):
		pass
		
class monitor_client (asynchat.async_chat):
	def __init__ (self, password, addr=('',8023), socket_type=socket.AF_INET):
		asynchat.async_chat.__init__ (self)
		self.create_socket (socket_type, socket.SOCK_STREAM)
		self.terminator = '\r\n'
		self.connect (addr)
		self.sent_auth = 0
		self.timestamp = ''
		self.password = password

	def collect_incoming_data (self, data):
		if not self.sent_auth:
			self.timestamp = self.timestamp + data
		else:
			sys.stdout.write (data)
			sys.stdout.flush()

	def found_terminator (self):
		if not self.sent_auth:
			self.push (hex_digest (self.timestamp + self.password) + '\r\n')
			self.sent_auth = 1
		else:
			print

	def handle_close (self):
		# close all the channels, which will make the standard main
		# loop exit.
		map (lambda x: x.close(), asyncore.socket_map.values())

	def log (self, *ignore):
		pass

class encrypted_monitor_client (monitor_client):
	"Wrap push() and recv() with a stream cipher"

	def init_cipher (self, cipher, key):
		self.outgoing = cipher.new (key)
		self.incoming = cipher.new (key)

	def push (self, data):
		# push the encrypted data instead
		return monitor_client.push (self, self.outgoing.encrypt (data))

	def recv (self, block_size):
		data = monitor_client.recv (self, block_size)
		if data:
			return self.incoming.decrypt (data)
		else:
			return data

def hex_digest (s):
	m = md5.md5()
	m.update (s)
	return string.join (
		map (lambda x: hex (ord (x))[2:], map (None, m.digest())),
		'',
		)

if __name__ == '__main__':
	if len(sys.argv) == 1:
		print 'Usage: %s host port' % sys.argv[0]
		sys.exit(0)

	if ('-e' in sys.argv):
		encrypt = 1
		sys.argv.remove ('-e')
	else:
		encrypt = 0

	sys.stderr.write ('Enter Password: ')
	sys.stderr.flush()
	import os
	try:
		os.system ('stty -echo')
		p = raw_input()
		print
	finally:
		os.system ('stty echo')
	stdin = stdin_channel (0)
	if len(sys.argv) > 1:
		if encrypt:
			client = encrypted_monitor_client (p, (sys.argv[1], string.atoi (sys.argv[2])))
			import sapphire
			client.init_cipher (sapphire, p)
		else:
			client = monitor_client (p, (sys.argv[1], string.atoi (sys.argv[2])))
	else:
		# default to local host, 'standard' port
		client = monitor_client (p)
	stdin.sock_channel = client
	asyncore.loop()
