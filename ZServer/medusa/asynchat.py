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

import socket
import asyncore
import string

# This class adds support for 'chat' style protocols - where one side
# sends a 'command', and the other sends a response (examples would be
# the common internet protocols - smtp, nntp, ftp, etc..).

# The handle_read() method looks at the input stream for the current
# 'terminator' (usually '\r\n' for single-line responses, '\r\n.\r\n'
# for multi-line output), calling self.found_terminator() on its
# receipt.

# for example:
# Say you build an async nntp client using this class.  At the start
# of the connection, you'll have self.terminator set to '\r\n', in
# order to process the single-line greeting.  Just before issuing a
# 'LIST' command you'll set it to '\r\n.\r\n'.  The output of the LIST
# command will be accumulated (using your own 'collect_incoming_data'
# method) up to the terminator, and then control will be returned to
# you - by calling your self.found_terminator() method

class async_chat (asyncore.dispatcher):
	"""This is an abstract class.  You must derive from this class, and add
	the two methods collect_incoming_data() and found_terminator()"""

	# these are overridable defaults

	ac_in_buffer_size	= 4096
	ac_out_buffer_size	= 4096

	def __init__ (self, conn=None):
		self.ac_in_buffer = ''
		self.ac_out_buffer = ''
		self.producer_fifo = fifo()
		asyncore.dispatcher.__init__ (self, conn)

	def set_terminator (self, term):
		"Set the input delimiter.  Can be a fixed string of any length, an integer, or None"
		self.terminator = term

	def get_terminator (self):
		return self.terminator

	# grab some more data from the socket,
	# throw it to the collector method,
	# check for the terminator,
	# if found, transition to the next state.

	def handle_read (self):

		try:
			data = self.recv (self.ac_in_buffer_size)
		except socket.error, why:
			self.handle_error()
			return

		self.ac_in_buffer = self.ac_in_buffer + data

		# Continue to search for self.terminator in self.ac_in_buffer,
		# while calling self.collect_incoming_data.  The while loop
		# is necessary because we might read several data+terminator
		# combos with a single recv(1024).

		while self.ac_in_buffer:
			lb = len(self.ac_in_buffer)
			terminator = self.get_terminator()
			if terminator is None:
				# no terminator, collect it all
				self.collect_incoming_data (self.ac_in_buffer)
				self.ac_in_buffer = ''
			elif type(terminator) == type(0):
				# numeric terminator
				n = terminator
				if lb < n:
					self.collect_incoming_data (self.ac_in_buffer)
					self.ac_in_buffer = ''
					self.terminator = self.terminator - lb
				else:
					self.collect_incoming_data (self.ac_in_buffer[:n])
					self.ac_in_buffer = self.ac_in_buffer[n:]
					self.terminator = 0
					self.found_terminator()
			else:
				# 3 cases:
				# 1) end of buffer matches terminator exactly:
				#    collect data, transition
				# 2) end of buffer matches some prefix:
				#    collect data to the prefix
				# 3) end of buffer does not match any prefix:
				#    collect data
				terminator_len = len(terminator)
				index = string.find (self.ac_in_buffer, terminator)
				if index != -1:
					# we found the terminator
					if index > 0:
						# don't bother reporting the empty string (source of subtle bugs)
						self.collect_incoming_data (self.ac_in_buffer[:index])
					self.ac_in_buffer = self.ac_in_buffer[index+terminator_len:]
					# This does the Right Thing if the terminator is changed here.
					self.found_terminator()
				else:
					# check for a prefix of the terminator
					index = find_prefix_at_end (self.ac_in_buffer, terminator)
					if index:
						if index != lb:
							# we found a prefix, collect up to the prefix
							self.collect_incoming_data (self.ac_in_buffer[:-index])
							self.ac_in_buffer = self.ac_in_buffer[-index:]
						break
					else:
						# no prefix, collect it all
						self.collect_incoming_data (self.ac_in_buffer)
						self.ac_in_buffer = ''

	def handle_write (self):
		self.initiate_send ()
		
	def handle_close (self):
		self.close()

	def push (self, data):
		self.producer_fifo.push (simple_producer (data))
		self.initiate_send()

	def push_with_producer (self, producer):
		self.producer_fifo.push (producer)
		self.initiate_send()

	def readable (self):
		"predicate for inclusion in the readable for select()"
		return (len(self.ac_in_buffer) <= self.ac_in_buffer_size)

	def writable (self):
		"predicate for inclusion in the writable for select()"
		# return len(self.ac_out_buffer) or len(self.producer_fifo) or (not self.connected)
		# this is about twice as fast, though not as clear.
		return not (
			(self.ac_out_buffer is '') and
			self.producer_fifo.is_empty() and
			self.connected
			)

	def close_when_done (self):
		"automatically close this channel once the outgoing queue is empty"
		self.producer_fifo.push (None)

	# refill the outgoing buffer by calling the more() method
	# of the first producer in the queue
	def refill_buffer (self):
		_string_type = type('')
		while 1:
			if len(self.producer_fifo):
				p = self.producer_fifo.first()
				# a 'None' in the producer fifo is a sentinel,
				# telling us to close the channel.
				if p is None:
					if not self.ac_out_buffer:
						self.producer_fifo.pop()
						self.close()
					return
				elif type(p) is _string_type:
					self.producer_fifo.pop()
					self.ac_out_buffer = self.ac_out_buffer + p
					return
				data = p.more()
				if data:
					self.ac_out_buffer = self.ac_out_buffer + data
					return
				else:
					self.producer_fifo.pop()
			else:
				return

	def initiate_send (self):
		obs = self.ac_out_buffer_size
		# try to refill the buffer
		if (len (self.ac_out_buffer) < obs):
			self.refill_buffer()

		if self.ac_out_buffer and self.connected:
			# try to send the buffer
			try:
				num_sent = self.send (self.ac_out_buffer[:obs])
				if num_sent:
					self.ac_out_buffer = self.ac_out_buffer[num_sent:]

			except socket.error, why:
				self.handle_error()
				return

	def discard_buffers (self):
		# Emergencies only!
		self.ac_in_buffer = ''
		self.ac_out_buffer = ''
		while self.producer_fifo:
			self.producer_fifo.pop()

class simple_producer:

	def __init__ (self, data, buffer_size=512):
		self.data = data
		self.buffer_size = buffer_size

	def more (self):
		if len (self.data) > self.buffer_size:
			result = self.data[:self.buffer_size]
			self.data = self.data[self.buffer_size:]
			return result
		else:
			result = self.data
			self.data = ''
			return result

class fifo:
	def __init__ (self, list=None):
		if not list:
			self.list = []
		else:
			self.list = list
		
	def __len__ (self):
		return len(self.list)

	def is_empty (self):
		return self.list == []

	def first (self):
		return self.list[0]

	def push (self, data):
		self.list.append (data)

	def pop (self):
		if self.list:
			result = self.list[0]
			del self.list[0]
			return (1, result)
		else:
			return (0, None)

# Given 'haystack', see if any prefix of 'needle' is at its end.  This
# assumes an exact match has already been checked.  Return the number of
# characters matched.
# for example:
# f_p_a_e ("qwerty\r", "\r\n") => 1
# f_p_a_e ("qwerty\r\n", "\r\n") => 2
# f_p_a_e ("qwertydkjf", "\r\n") => 0

# this could maybe be made faster with a computed regex?

##def find_prefix_at_end (haystack, needle):
##	nl = len(needle)
##	result = 0
##	for i in range (1,nl):
##		if haystack[-(nl-i):] == needle[:(nl-i)]:
##			result = nl-i
##			break
##	return result

# yes, this is about twice as fast, but still seems
# to be neglible CPU.  The previous could do about 290
# searches/sec. the new one about 555/sec.

import regex

prefix_cache = {}

def prefix_regex (needle):
	if prefix_cache.has_key (needle):
		return prefix_cache[needle]
	else:
		reg = needle[-1]
		for i in range(1,len(needle)):
			reg = '%c\(%s\)?' % (needle[-(i+1)], reg)
		reg = regex.compile (reg+'$')
		prefix_cache[needle] = reg, len(needle)
		return reg, len(needle)

def find_prefix_at_end (haystack, needle):
	reg, length = prefix_regex (needle)
	lh = len(haystack)
	result = reg.search (haystack, max(0,lh-length))
	if result >= 0:
		return (lh - result)
	else:
		return 0
