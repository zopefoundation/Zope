# -*- Mode: Python; tab-width: 4 -*-

import asynchat
import socket
import string

#
# three types of log:
# 1) file
#    with optional flushing.
# 2) socket
#    dump output directly to a socket connection. [how do we
#    keep it open?]
# 3) syslog
#    log to syslog via tcp.  this is a per-line protocol.
#

#
# The 'standard' interface to a logging object is simply
# log_object.log (message)
#

# a file-like object that captures output, and
# makes sure to flush it always...  this could
# be connected to:
#  o	stdio file
#  o	low-level file
#  o	socket channel
#  o	syslog output...

class file_logger:
			
	# pass this either a path or a file object.
	def __init__ (self, file, flush=1, mode='wa'):
		if type(file) == type(''):
			if (file == '-'):
				import sys
				self.file = sys.stdout
			else:
				self.file = open (file, mode)
		else:
			self.file = file
		self.do_flush = flush

	def __repr__ (self):
		return '<file logger: %s>' % self.file

	def write (self, data):
		self.file.write (data)
		self.maybe_flush()
		
	def writeline (self, line):
		self.file.writeline (line)
		self.maybe_flush()
		
	def writelines (self, lines):
		self.file.writelines (lines)
		self.maybe_flush()

	def maybe_flush (self):
		if self.do_flush:
			self.file.flush()

	def flush (self):
		self.file.flush()

	def softspace (self, *args):
		pass

	def log (self, message):
		if message[-1] not in ('\r', '\n'):
			self.write (message + '\n')
		else:
			self.write (message)

# syslog is a line-oriented log protocol - this class would be
# appropriate for FTP or HTTP logs, but not for dumping stderr to.

# TODO: a simple safety wrapper that will ensure that the line sent
# to syslog is reasonable.

# TODO: async version of syslog_client: now, log entries use blocking
# send()

import m_syslog
syslog_logger = m_syslog.syslog_client

class syslog_logger (m_syslog.syslog_client):
	def __init__ (self, address, facility='user'):
		m_syslog.syslog_client.__init__ (self, address)
		self.facility = m_syslog.facility_names[facility]
		self.address=address

	def __repr__ (self):
		return '<syslog logger address=%s>' % (repr(self.address))

	def log (self, message):
		m_syslog.syslog_client.log (
			self,
			message,
			facility=self.facility,
			priority=m_syslog.LOG_INFO
			)

# log to a stream socket, asynchronously

class socket_logger (asynchat.async_chat):

	def __init__ (self, address):

		if type(address) == type(''):
			self.create_socket (socket.AF_UNIX, socket.SOCK_STREAM)
		else:
			self.create_socket (socket.AF_INET, socket.SOCK_STREAM)

		self.connect (address)
		self.address = address
		
	def __repr__ (self):
		return '<socket logger: address=%s>' % (self.address)

	def log (self, message):
		if message[-2:] != '\r\n':
			self.socket.push (message + '\r\n')
		else:
			self.socket.push (message)

# log to multiple places
class multi_logger:
	def __init__ (self, loggers):
		self.loggers = loggers

	def __repr__ (self):
		return '<multi logger: %s>' % (repr(self.loggers))

	def log (self, message):
		for logger in self.loggers:
			logger.log (message)

class resolving_logger:
	"""Feed (ip, message) combinations into this logger to get a
	resolved hostname in front of the message.  The message will not
	be logged until the PTR request finishes (or fails)."""

	def __init__ (self, resolver, logger):
		self.resolver = resolver
		self.logger = logger

	class logger_thunk:
		def __init__ (self, message, logger):
			self.message = message
			self.logger = logger

		def __call__ (self, host, ttl, answer):
			if not answer:
				answer = host
			self.logger.log ('%s:%s' % (answer, self.message))

	def log (self, ip, message):
		self.resolver.resolve_ptr (
			ip,
			self.logger_thunk (
				message,
				self.logger
				)
			)

class unresolving_logger:
	"Just in case you don't want to resolve"
	def __init__ (self, logger):
		self.logger = logger

	def log (self, ip, message):
		self.logger.log ('%s:%s' % (ip, message))


def strip_eol (line):
	while line and line[-1] in '\r\n':
		line = line[:-1]
	return line

class tail_logger:
	"Keep track of the last <size> log messages"
	def __init__ (self, logger, size=500):
		self.size = size
		self.logger = logger
		self.messages = []

	def log (self, message):
		self.messages.append (strip_eol (message))
		if len (self.messages) > self.size:
			del self.messages[0]
		self.logger.log (message)
