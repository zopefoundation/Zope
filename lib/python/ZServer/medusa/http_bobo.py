# -*- Mode: Python; tab-width: 4 -*-

import string
import regex

RCS_ID = '$Id: http_bobo.py,v 1.2 2001/04/25 19:07:31 andreas Exp $'
VERSION_STRING = string.split(RCS_ID)[2]

class bobo_extension:
	hits = 0

	SERVER_IDENT = 'Bobo Extension (V%s)' % VERSION_STRING

	def __init__ (self, regexp):
		self.regexp = regex.compile (regexp)

	def __repr__ (self):
		return '<Bobo Extension <b>(%d hits)</b> at %x>' % (
			self.hits,
			id (self)
			)

	def match (self, path_part):
		if self.regexp.match (path_part) == len(path_part):
			return 1
		else:
			return 0

	def status (self):
		return mstatus.lines_producer ([
			'<h2>%s</h2>'  						%self.SERVER_IDENT,
			'<br><b>Total Hits:</b> %d'			% self.hits,
			]

	def handle_request (self, channel):
		self.hits = self.hits + 1

		[path, params, query, fragment] = channel.uri

		if query:
			# cgi_publisher_module doesn't want the leading '?'
			query = query[1:]

		env = {}
		env['REQUEST_METHOD']	= method
		env['SERVER_PORT']		= channel.server.port
		env['SERVER_NAME']		= channel.server.server_name
		env['SCRIPT_NAME']		= module_name
		env['QUERY_STRING']		= query
		env['PATH_INFO']		= string.join (path_parts[1:],'/')

		# this should really be done with with a real producer.  just
		# have to make sure it can handle all of the file object api.

		sin  = StringIO.StringIO('')
		sout = StringIO.StringIO()
		serr = StringIO.StringIO()

		cgi_module_publisher.publish_module (
			module_name,
			stdin=sin,
			stdout=sout,
			stderr=serr,
			environ=env,
			debug=1
			)
		
		channel.push (
			channel.response (200) + \
			channel.generated_content_header (path)
			)

		self.push (sout.getvalue())
		self.push (serr.getvalue())
		self.close_when_done()
