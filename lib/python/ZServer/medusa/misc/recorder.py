# -*- Mode: Python; tab-width: 4 -*-

# This server can be used to record HTTP requests for debugging.

import socket
import asyncore
import asynchat

class recorder_channel (asyncore.dispatcher):
	def __init__ (self, sock, addr):
		asyncore.dispatcher.__init__ (self, sock)
		self.fd = open ('%s:%d' % addr, 'wb')

	def handle_read (self):
		data = self.recv (1024)
		if not data:
			self.fd.close()
			self.close()
		else:
			self.fd.write (data)
			self.fd.flush()

class recorder_server (asyncore.dispatcher):

	SERVER_IDENT = 'Recorder'

	def __init__ (self, port=8989):
		self.create_socket (socket.AF_INET, socket.SOCK_STREAM)
		self.bind (('', port))
		print '%s started on port %d' % (self.SERVER_IDENT, port)
		self.listen (5)
		
	def handle_accept (self):
		conn, addr = self.accept()
		print 'incoming connection',addr
		recorder_channel (conn, addr)

# force a clean shutdown
def shutdown():
	sm = asyncore.socket_map
	asyncore.socket_map = {}
	for s in sm.values():
		try:
			s.close()
		except:
			pass
	print 'Done.'


if __name__ == '__main__':
	import string
	import sys
	if len(sys.argv) > 1:
		port = string.atoi (sys.argv[1])
	else:
		port = 8989
	s = recorder_server (port)
	try:
		asyncore.loop()
	except KeyboardInterrupt:
		import sys
		import tb
		print sys.exc_type, sys.exc_value
		tb.printtb (sys.exc_traceback)
		print 'Shutting down due to unhandled exception...'
		shutdown()
