"""ZServer FTP Channel for use the medusa's ftp server.

"""

from PubCore import handle
from medusa.ftp_server import ftp_channel, ftp_server
from medusa import asynchat, filesys
from medusa.producers import NotReady
from cStringIO import StringIO
import string
import os
from regsub import gsub
from base64 import encodestring
from mimetypes import guess_type
import marshal
import stat
import time

class zope_ftp_channel(ftp_channel):
	"Passes its commands to Zope, not a filesystem"
	
	read_only=0
	
	def __init__ (self, server, conn, addr, module):
		ftp_channel.__init__(self,server,conn,addr)
		self.module=module
		self.userid=''
		self.password=''
		self.path='/'

	def _get_env(self):
		"Returns a CGI style environment"
		env={}
		env['SCRIPT_NAME']='/%s' % self.module
		env['PATH_INFO']=self.path
		env['REQUEST_METHOD']='GET' # XXX what should this be?
		env['SERVER_SOFTWARE']=self.server.SERVER_IDENT
		if self.userid != 'anonymous':
			env['HTTP_AUTHORIZATION']='Basic %s' % gsub('\012','',
					encodestring('%s:%s' % (self.userid,self.password)))
		env['BOBO_DEBUG_MODE']='1'
		env['SERVER_NAME']=self.server.hostname
		env['SERVER_PORT']=str(self.server.port)
		env['REMOTE_ADDR']=self.client_addr[0]
		env['GATEWAY_INTERFACE']='CGI/1.1' # that's stretching it ;-)
		
		# XXX etcetera -- probably set many of these at the start

		return env
		

		
	def _join_paths(self,*args):
		path=apply(os.path.join,args)
		path=os.path.normpath(path)
		if os.sep != '/':
			path=string.replace(path,os.sep,'/')
		return path
		
	def make_response(self,resp):
		self.log ('==> %s' % resp)
		return resp + '\r\n'
	
	# Overriden async_chat methods
	
	writable=asynchat.async_chat.writable_future
	
	# Overriden ftp_channel methods

	def cmd_nlst (self, line):
		'give name list of files in directory'
		self.push_with_producer(self.get_dir_list (line, 0))

	def cmd_list (self, line):
		'give list files in a directory'
		
		# XXX should handle listing a file, not just a directory
		#     also should maybe glob, but this is hard to do...
		
		self.push_with_producer(self.get_dir_list (line, 1))
	
	def get_dir_list (self, line, long=0):
		# we need to scan the command line for arguments to '/bin/ls'...
		# XXX clean this up
		if len(line) > 1:
			args = string.split(line[1])
		else:
			args =[]
		path_args = []
		for arg in args:
			if arg[0] != '-':
				path_args.append (arg)
			else:
				if 'l' in arg:
					long=1
		if len(path_args) < 1:
			dir = '.'
		else:
			dir = path_args[0]
		return self.listdir (dir, long)
	
	def listdir (self, path, long=0):
		env=self._get_env()
		env['PATH_INFO']=self._join_paths(self.path,path,'manage_FTPlist')
		outpipe=handle(self.module,env,StringIO())
		return ResponseProducer(outpipe,self._do_listdir,(long,))			
		
	def _do_listdir(self,long,response):
		#print "do list response", response.__dict__
		code=response.headers['Status'][:3]
		if code=='200':
			dir_list=''
			file_infos=marshal.loads(response.content)
			if type(file_infos[0])==type(''):
				file_infos=(file_infos,)	
			if long:
				for id, stat_info in file_infos:
					dir_list=dir_list+filesys.unix_longify(id,stat_info)+'\r\n'
			else:
				for id, stat_info in file_infos:
					dir_list=dir_list+id+'\r\n'
			self.make_xmit_channel()
			self.client_dc.push(dir_list)
			self.client_dc.close_when_done()				
			return 	self.make_response(
				'150 Opening %s mode data connection for file list' % (
					self.type_map[self.current_mode]
					)
				)	
		elif code=='401':
			return self.make_response('530 Unauthorized.')
		else:
			return self.make_response('550 Could not list directory.')

	def cmd_cwd (self, line):
		'change working directory'
		# try to call manage_FTPlist on the path
		env=self._get_env()
		path=line[1]
		path=self._join_paths(self.path,path,'manage_FTPlist')
		env['PATH_INFO']=path
		outpipe=handle(self.module,env,StringIO())
		self.push_with_producer(ResponseProducer
				(outpipe,self._cmd_cwd,(path[:-15],)))			

	def _cmd_cwd(self,path,response):
		code=response.headers['Status'][:3]
		if code=='200':
			listing=marshal.loads(response.content)
			# check to see if we are cding to a non-foldoid object
			if type(listing[0])==type(''):
				return self.make_response('550 No such directory.')
			self.path=path or '/'
			return self.make_response('250 CWD command successful.')
		elif code=='401':
			return self.make_response('530 Unauthorized.')
		else:
			return self.make_response('550 No such directory.')

	def cmd_cdup (self, line):
		'change to parent of current working directory'
		self.cmd_cwd((None,'..'))

	def cmd_pwd (self, line):
		'print the current working directory'
		self.respond (
			'257 "%s" is the current directory.' % (
				self.path
				)
			)
	
	cmd_xpwd=cmd_pwd
	
	def cmd_mdtm (self, line):
		'show last modification time of file'
		if len (line) != 2:
			self.command.not_understood (string.join (line))
			return
		env=self._get_env()
		env['PATH_INFO']=self._join_paths(self.path,line[1],'manage_FTPstat')
		outpipe=handle(self.module,env,StringIO())
		self.push_with_producer(ResponseProducer(outpipe, self._cmd_mdtm))
	
	def _cmd_mdtm(self,response):
		#print "mdtm response", response.__dict__
		code=response.headers['Status'][:3]
		if code=='200':
			mtime=marshal.loads(response.content)[stat.ST_MTIME]
			mtime=time.gmtime(mtime)
			return self.make_response('213 %4d%02d%02d%02d%02d%02d' % (
								mtime[0],
								mtime[1],
								mtime[2],
								mtime[3],
								mtime[4],
								mtime[5]
								))
		elif code=='401':
			return self.make_response('530 Unauthorized.') 
		else:
			return self.make_response('550 Error getting file modification time.')	
				
	def cmd_size (self, line):
		'return size of file'
		if len (line) != 2:
			self.command.not_understood (string.join (line))
			return
		env=self._get_env()
		env['PATH_INFO']=self._join_paths(self.path,line[1],'manage_FTPstat')
		outpipe=handle(self.module,env,StringIO())
		self.push_with_producer(ResponseProducer(outpipe, self._cmd_size))

	def _cmd_size(self,response):
		#print "size response", response.__dict__
		code=response.headers['Status'][:3]
		if code=='200':
			return self.make_response('213 %d'% 
					marshal.loads(response.content)[stat.ST_SIZE])
		elif code=='401':
			return self.make_response('530 Unauthorized.') 
		else:
			return self.make_response('550 Error getting file size.')	
			
			self.client_dc.close_when_done()

	def cmd_retr(self,line):
		if len(line) < 2:
			self.command_not_understood (string.join (line))
			return
		env=self._get_env()
		path,id=os.path.split(line[1])
		env['PATH_INFO']=self._join_paths(self.path,line[1],'manage_FTPget')
		outpipe=handle(self.module,env,StringIO())
		self.push_with_producer(ResponseProducer(outpipe,
									self._cmd_retr, (line[1],)))	

	def _cmd_retr(self,file,response):
		#print "retr response\n", response.__dict__
		code=response.headers['Status'][:3]
		if code=='200':
			#fd=StringIO(response.content)
			self.make_xmit_channel()
			#if self.restart_position:
			#	# try to position the file as requested, but
			#	# give up silently on failure (the 'file object'
			#	# may not support seek())
			#	try:
			#		fd.seek (self.restart_position)
			#	except:
			#		pass
			#	self.restart_position = 0
			self.client_dc.push(response.content)
			self.client_dc.close_when_done()
			return self.make_response(
					"150 Opening %s mode data connection for file '%s'" % (
						self.type_map[self.current_mode],
						file
						))
		elif code=='401':
			return self.make_response('530 Unauthorized.')
		else:
			return self.make_response('550 Error opening file.')	

	def cmd_stor (self, line, mode='wb'):
		'store a file'
		if len (line) < 2:
			self.command_not_understood (string.join (line))
			return
		elif self.restart_position:
				restart_position = 0
				self.respond ('553 restart on STOR not yet supported')
				return
			
		# XXX Check for possible problems first? Like authorization...
		#     But how? Once we agree to receive the file, can we still
		#     bail later?
		
		fd=ContentReceiver(self._do_cmd_stor,
				(self._join_paths(self.path,line[1]),))
		self.respond (
			'150 Opening %s connection for %s' % (
				self.type_map[self.current_mode],
				line[1]
				)
			)
		self.make_recv_channel (fd)
		
	def _do_cmd_stor(self,path,data):
		'callback to do the STOR, after we have the input'
		#print "stor callback", path, data
		env=self._get_env()
		env['PATH_INFO']=path
		env['REQUEST_METHOD']='PUT'
		ctype=guess_type(path)[0]
		if ctype is not None:
			env['CONTENT_TYPE']=ctype
		env['CONTENT_LENGTH']=len(data.getvalue())
		outpipe=handle(self.module,env,data)
		self.push_with_producer(ResponseProducer(outpipe, self._cmd_stor))			
				
	def _cmd_stor(self,response):
		code=response.headers['Status'][:3]
		if code in ('200','204','302'):
			return self.make_response('257 STOR command successful.')
		elif code=='401':
			return self.make_response('530 Unauthorized.')
		else:
			return self.make_response('550 Error creating file.')		
		
	def cmd_dele(self, line):
		if len (line) != 2:
			self.command.not_understood (string.join (line))
			return
		path,id=os.path.split(line[1])
		env=self._get_env()
		env['PATH_INFO']=self._join_paths(self.path,path,'manage_delObjects')
		env['QUERY_STRING']='ids=%s' % id
		outpipe=handle(self.module,env,StringIO())
		self.push_with_producer(ResponseProducer(outpipe, self._cmd_dele))
		
	def _cmd_dele(self,response):	
		code=response.headers['Status'][:3]
		if code=='200' and string.find(response.content,'Not Deletable')==-1:
			return self.make_response('250 DELE command successful.')
		elif code=='401':
			return self.make_response('530 Unauthorized.') 
		else:
			return self.make_response('550 Error deleting file.')		

	def cmd_mkd (self, line):
		if len (line) != 2:
			self.command.not_understood (string.join (line))
			return
		env=self._get_env()
		path,id=os.path.split(line[1])
		env['PATH_INFO']=self._join_paths(self.path,path,'manage_addFolder')
		env['QUERY_STRING']='id=%s' % id
		outpipe=handle(self.module,env,StringIO())
		self.push_with_producer(ResponseProducer(outpipe, self._cmd_mkd))	
	
	cmd_xmkd=cmd_mkd
	
	def _cmd_mkd(self,response):
		#print "mkd response", response.__dict__
		code=response.headers['Status'][:3]
		if code=='200':
			return self.make_response('257 MKD command successful.')
		elif code=='401':
			return self.make_response('530 Unauthorized.')
		else:
			return self.make_response('550 Error creating directory.')

	def cmd_rmd (self, line):
		# XXX should object be checked to see if it's folderish
		#     before we allow it to be RMD'd?
		if len (line) != 2:
			self.command.not_understood (string.join (line))
			return
		path,id=os.path.split(line[1])
		env=self._get_env()
		env['PATH_INFO']=self._join_paths(self.path,path,'manage_delObjects')
		env['QUERY_STRING']='ids=%s' % id
		outpipe=handle(self.module,env,StringIO())
		self.push_with_producer(ResponseProducer(outpipe, self._cmd_rmd))	

	cmd_xrmd=cmd_rmd

	def _cmd_rmd(self,response):
		#print "rmd response", response.__dict__
		code=response.headers['Status'][:3]
		if code=='200' and string.find(response.content,'Not Deletable')==-1:
			return self.make_response('250 RMD command successful.')
		elif code=='401':
			return self.make_response('530 Unauthorized.') 
		else:
			return self.make_response('550 Error removing directory.')			

	def cmd_user (self, line):
		'specify user name'
		if len(line) > 1:
			self.userid = line[1]
			self.respond ('331 Password required.')
		else:
			self.command_not_understood (string.join (line))

	def cmd_pass (self, line):
		'specify password'
		if len(line) < 2:
			pw = ''
		else:
			pw = line[1]
		self.password=pw
		self.respond ('230 Login successful.')
		self.authorized = 1
		self.log ('Successful login.')

	
class ZResponseReceiver:
	"""Given an output pipe reads response and parses it.
	After a call to ready returns true, you can read
	the headers as a dictiony and the content as a string."""
	
	def __init__(self,pipe):
		self.pipe=pipe
		self.data=''
		self.headers={}
		self.content=''
		
	def ready(self):
		if self.pipe is None:
			return 1
		if self.pipe.ready():
			data=self.pipe.read()
			if data:
				self.data=self.data+data
			else:
				self.parse()
				return 1
		
	def parse(self):
		headers,html=string.split(self.data,'\n\n',1)
		self.data=''
		for header in string.split(headers,'\n'):
			k,v=string.split(header,': ',1)
			self.headers[k]=v
		self.content=html
		self.pipe=None

	
class ResponseProducer:
	"Allows responses which need to make Zope requests first."
	
	def __init__(self,pipe,callback,args=None):
		self.response=ZResponseReceiver(pipe)
		self.callback=callback
		self.args=args or ()
		self.done=None
		
	def ready(self):
		if self.response is not None:
			return self.response.ready()
		else:
			return 1
	
	def more(self):
		if not self.done:
			if not self.response.ready():
				raise NotReady()
			self.done=1
			r=self.response
			c=self.callback
			args=self.args+(r,)
			self.response=None
			self.callback=None
			self.args=None
			return apply(c,args)
		else:
			return ''
			
	
class ContentReceiver:
	"Write-only file object used to receive data from FTP"
	
	def __init__(self,callback,args=None):
		self.data=StringIO()
		self.callback=callback
		self.args=args or ()
		
	def write(self,data):
		self.data.write(data)
	
	def close(self):
		self.data.seek(0)
		args=self.args+(self.data,)
		c=self.callback
		self.callback=None
		self.args=None
		apply(c,args)
		
class zope_ftp_server(ftp_server):
	ftp_channel_class = zope_ftp_channel

	def __init__(self,module,hostname,port,resolver,logger_object):
		ftp_server.__init__(self,None,hostname,port,resolver,logger_object)
		self.module=module
		
	def handle_accept (self):
		conn, addr = self.accept()
		self.total_sessions.increment()
		print 'Incoming connection from %s:%d' % (addr[0], addr[1])
		self.ftp_channel_class (self, conn, addr, self.module)	
	