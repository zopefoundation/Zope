"""Bobo handler module
For use with medusa & python object publisher

copyright 1997 amos latteier
(code based on script_handler.py)

Use:

here is a sample fragment from a script to start medusa:

...
hs = http_server.http_server (IP_ADDRESS, HTTP_PORT, rs, lg)
...
sys.path.insert(0,'c:\\windows\\desktop\\medusa2\\www\\bobo')
import bobotest
bh=bobo_handler.bobo_handler(bobotest, debug=1)	#create bobo handler	
hs.install_handler(bh)	#install handler in http server
...

This will install the bobo handler on the http server and give you 
access to the bobotest module via urls like this:

http://myserver.com/bobotest/blah/blah

bobo_handler initalization options: 
* debug: If the debug flag is set then the published module will be reloaded
whenever its source is changed on disk. This is very handy for developement.
* uri_base: If the uri_base isn't specified it defaults to /<module_name>
"""

__version__="1.03"

import cgi_module_publisher
import sys
import regex
import string
import os

try:
	from cStringIO import StringIO
except:
	from StringIO import StringIO
try:
	import thread
  	mutex = thread.allocate_lock()
	THREADS = 1
except:
	THREADS = 0

import counter
import default_handler
import producers

split_path = default_handler.split_path
unquote    = default_handler.unquote
get_header = default_handler.get_header

CONTENT_LENGTH = regex.compile ('Content-Length: \([0-9]+\)', regex.casefold)


# maps request headers to environment variables
#

header2env={'Content-Length'	: 'CONTENT_LENGTH',
			'Content-Type'		: 'CONTENT_TYPE',
			'Referer'			: 'HTTP_REFERER',
			'User-Agent'		: 'HTTP_USER_AGENT',
			'Accept'			: 'HTTP_ACCEPT',
			'Accept-Charset'	: 'HTTP_ACCEPT_CHARSET',
			'Accept-Language'	: 'HTTP_ACCEPT_LANGUAGE',
			'Host'				: None,
			'Connection'		: 'CONNECTION_TYPE',
			'Pragma'			: None,
			'Authorization'		: 'HTTP_AUTHORIZATION',
			'Cookie'			: 'HTTP_COOKIE',
			}
# convert keys to lower case for case-insensitive matching
#
for (key,value) in header2env.items():
	del header2env[key]
	key=string.lower(key)
	header2env[key]=value


class bobo_handler:
	"publishes a module via bobo"
	
	def __init__ (self, module, uri_base=None, debug=None):
		self.module = module
		self.debug = debug
		if self.debug:
			self.last_reload=self.module_mtime()
		self.hits = counter.counter()
		
		# if uri_base is unspecified, assume it
		# starts with the published module name
		#
		if not uri_base:	
			uri_base="/%s" % module.__name__
		elif uri_base[-1]=="/":	# kill possible trailing /
			uri_base=uri_base[:-1]
		self.uri_base=uri_base
		
		uri_regex='%s.*' % self.uri_base
		self.uri_regex = regex.compile(uri_regex)
		

	def match (self, request):
		uri = request.uri
		if self.uri_regex.match (uri) == len(uri):
			return 1
		else:
			return 0

	def handle_request (self, request):
		[path, params, query, fragment] = split_path (request.uri)
		while path and path[0] == '/':
			path = path[1:]

		if '%' in path:
			path = unquote (path)

		self.hits.increment()

		if query:
			# cgi_publisher_module doesn't want the leading '?'
			query = query[1:]
		
		self.env = {}
		self.env['REQUEST_METHOD']	= string.upper(request.command)
		self.env['SERVER_PORT']		= '%s' % request.channel.server.port
		self.env['SERVER_NAME']		= request.channel.server.server_name
		self.env['SERVER_SOFTWARE']	= request['Server']
		self.env['SCRIPT_NAME']		= self.uri_base  # are script_name and path_info ok?
		self.env['QUERY_STRING']	= query
		try:
			path_info=string.split(path,self.uri_base[1:],1)[1]
		except:
			path_info=''
		self.env['PATH_INFO']		= path_info
		self.env['GATEWAY_INTERFACE']='CGI/1.1'			# what should this really be?
		self.env['REMOTE_ADDR']=request.channel.addr[0]
		self.env['REMOTE_HOST']=request.channel.addr[0]	#what should this be?

		for header in request.header:
			[key,value]=string.split(header,": ",1)
			key=string.lower(key)
			if header2env.has_key(key):
				if header2env[key]:
					self.env[header2env[key]]=value
			else:
				key='HTTP_'+string.upper(string.join(string.split(key,"-"),"_"))
				self.env[key]=value

		# remove empty environment variables
		#
		for key in self.env.keys():
			if self.env[key]=="" or self.env[key]==None:
				del self.env[key]

		if request.command in ["post","put"]:
			request.collector=input_collector(self,request)
			request.channel.set_terminator (None)
		else:
			sin=StringIO('')
			self.continue_request(sin,request)
		

	def continue_request(self,sin,request):
		"continue handling request now that we have the stdin"
		
		# if we have threads spawn a new one to publish the module
		# so we dont freeze the server while publishing.
		if THREADS:
			thread.start_new_thread(self._continue_request,(sin,request))
		else:
			self._continue_request(sin,request)
			

	def _continue_request(self,sin,request):
		"continue handling request now that we have the stdin"
		sout = StringIO()
		serr = StringIO()

		if self.debug:
			m_time=self.module_mtime()
			if m_time> self.last_reload:
				reload(self.module)
				self.last_reload=m_time
		if THREADS:
			mutex.acquire()
		cgi_module_publisher.publish_module(
			self.module.__name__,
			stdin=sin,
			stdout=sout,
			stderr=serr,
			environ=self.env,
			#debug=1
			)
		if THREADS:
			mutex.release()

		if serr.tell():
			request.log(serr.getvalue())
		
		response=sout
		response=response.getvalue()

		# set response headers
		[headers,html]=string.split(response,"\n\n",1)
		headers=string.split(headers,"\n")

		for line in headers:
			[header, header_value]=string.split(line,": ",1)
			if header=="Status":
				[code,message]=string.split(header_value," ",1)
				request.reply_code=string.atoi(code)
			else:
				request[header]=header_value

		request.push(html)
		request.done()


	def module_mtime(self):
		"returns the last modified date for a given module's source file"
		return os.stat(self.module.__file__)[8]

	def status (self):
		return producers.simple_producer (
			'<li>Bobo Handler'
			+ '<ul>'
			+ '  <li><b>Hits:</b> %d' % int(self.hits)
			+ '</ul>'
			)


class input_collector:
	"gathers input for put and post requests"

	def __init__ (self, handler, request):
		self.handler	= handler
		self.request	= request
		self.data = StringIO()
		
		# make sure there's a content-length header
		self.cl = get_header (CONTENT_LENGTH, request.header)
		
		if not self.cl:
			request.error(411)
			return
		else:
			self.cl = string.atoi(self.cl)

	def collect_incoming_data (self, data):
		self.data.write(data)
		if self.data.tell() >= self.cl:
			self.data.seek(0)

			h=self.handler
			r=self.request

			# set the terminator back to the default
			self.request.channel.set_terminator ('\r\n\r\n')
			del self.handler
			del self.request

			h.continue_request(self.data,r)


