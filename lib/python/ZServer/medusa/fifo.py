# -*- Mode: Python; tab-width: 4 -*-

# fifo, implemented with lisp-style pairs.
# [quick translation of scheme48/big/queue.scm]
	
class fifo:

	def __init__ (self):
		self.head, self.tail = None, None
		self.length = 0
		self.node_cache = None
		
	def __len__ (self):
		return self.length

	def push (self, v):
		self.node_cache = None
		self.length = self.length + 1
		p = [v, None]
		if self.head is None:
			self.head = p
		else:
			self.tail[1] = p
		self.tail = p

	def pop (self):
		self.node_cache = None
		pair = self.head
		if pair is None:
			raise ValueError, "pop() from an empty queue"
		else:
			self.length = self.length - 1
			[value, next] = pair
			self.head = next
			if next is None:
				self.tail = None
			return value

	def first (self):
		if self.head is None:
			raise ValueError, "first() of an empty queue"
		else:
			return self.head[0]

	def push_front (self, thing):
		self.node_cache = None
		self.length = self.length + 1
		old_head = self.head
		new_head = [thing, old_head]
		self.head = new_head
		if old_head is None:
			self.tail = new_head

	def _nth (self, n):
		i = n
		h = self.head
		while i:
			h = h[1]
			i = i - 1
		self.node_cache = n, h[1]
		return h[0]

	def __getitem__ (self, index):
		if (index < 0) or (index >= self.length):
			raise IndexError, "index out of range"
		else:
			if self.node_cache:
				j, h = self.node_cache
				if j == index - 1:
					result = h[0]
					self.node_cache = index, h[1]
					return result
				else:
					return self._nth (index)
			else:
				return self._nth (index)

			
class protected_fifo:
	
	def __init__ (self, lock=None):
		if lock is None:
			import thread
			self.lock = thread.allocate_lock()
		else:
			self.lock = lock
		self.fifo = fifo.fifo()

	def push (self, item):
		try:
			self.lock.acquire()
			self.fifo.push (item)
		finally:
			self.lock.release()

	enqueue = push

	def pop (self):
		try:
			self.lock.acquire()
			return self.fifo.pop()
		finally:
			self.lock.release()

	dequeue = pop
	
	def __len__ (self):
		try:
			self.lock.acquire()
			return len(self.queue)
		finally:
			self.lock.release()

class output_fifo:
	
	EMBEDDED	= 'embedded'
	EOF			= 'eof'
	TRIGGER		= 'trigger'

	def __init__ (self):
		# containment, not inheritance
		self.fifo = fifo()
		self._embedded = None

	def push_embedded (self, fifo):
		# push embedded fifo
		fifo.parent = self # CYCLE
		self.fifo.push ((self.EMBEDDED, fifo))

	def push_eof (self):
		# push end-of-fifo
		self.fifo.push ((self.EOF, None))

	def push_trigger (self, thunk):
		self.fifo.push ((self.TRIGGER, thunk))

	def push (self, item):
		# item should be a producer or string
		self.fifo.push (item)

	# 'length' is an inaccurate term.  we should
	# probably use an 'empty' method instead.
	def __len__ (self):
		if self._embedded is None:
			return len(self.fifo)
		else:
			return len(self._embedded)

	def empty (self):
		return len(self) == 0

	def first (self):
		if self._embedded is None:
			return self.fifo.first()
		else:
			return self._embedded.first()

	def pop (self):
		if self._embedded is not None:
			return self._embedded.pop()
		else:
			result = self.fifo.pop()
			# unset self._embedded
			self._embedded = None
			# check for special items in the front
			if len(self.fifo):
				front = self.fifo.first()
				if type(front) is type(()):
					# special
					kind, value = front
					if kind is self.EMBEDDED:
						self._embedded = value
					elif kind is self.EOF:
						# break the cycle
						parent = self.parent
						self.parent = None
						# pop from parent
						parent._embedded = None
					elif kind is self.TRIGGER:
						# call the trigger thunk
						value()
					# remove the special
					self.fifo.pop()
			# return the originally popped result
			return result

def test_embedded():
	of = output_fifo()
	f2 = output_fifo()
	f3 = output_fifo()
	of.push ('one')
	of.push_embedded (f2)
	f2.push ('two')
	f3.push ('three')
	f3.push ('four')
	f2.push_embedded (f3)
	f3.push_eof()
	f2.push ('five')
	f2.push_eof()
	of.push ('six')
	of.push ('seven')
	while 1:
		print of.pop()
