# -*- Mode: Python; tab-width: 4 -*-

RCS_ID = '$Id: asynchat_sendfile.py,v 1.2 2001/04/25 19:09:54 andreas Exp $'

import sendfile
import asynchat

async_chat = asynchat.async_chat

# we can't call sendfile() until ac_out_buffer is empty.

class async_chat_with_sendfile (async_chat):

	# if we are in the middle of sending a file, this will be overriden
	_sendfile = None

	def push_sendfile (self, fd, offset, bytes, callback=None):
		# we set out_buffer_size to zero in order to keep async_chat
		# from calling refill_buffer until the whole file has been sent.
		self._saved_obs = self.ac_out_buffer_size
		self.ac_out_buffer_size = 0
		self._sendfile = (fd, offset, bytes, callback)

	def initiate_send (self):
		if self._sendfile is None:
			async_chat.initiate_send (self)
		else:
			if len(self.ac_out_buffer):
				async_chat.initiate_send (self)
			else:
				fd, offset, bytes, callback = self._sendfile
				me = self.socket.fileno()
				try:
					sent = sendfile.sendfile (fd, me, offset, bytes)
					offset = offset + sent
					bytes = bytes - sent
					if bytes:
						self._sendfile = (fd, offset, bytes, callback)
					else:
						self._sendfile = None
						self.ac_out_buffer_size = self._saved_obs
						if callback is not None:
							# success
							callback (1, fd)
				except:
					self._sendfile = None
					self.ac_out_buffer_size = self._saved_obs
					# failure
					if callback is not None:
						callback (0, fd)

# here's how you might use this:
# fd = os.open (filename, os.O_RDONLY, 0644)
# size = os.lseek (fd, 0, 2)
# os.lseek (fd, 0, 0)
# self.push ('%08x' % size)
# self.push_sendfile (fd, 0, size)
