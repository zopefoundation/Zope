##############################################################################
# 
# Zope Public License (ZPL) Version 0.9.6
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
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
# 3. Any use, including use of the Zope software to operate a website,
#    must either comply with the terms described below under
#    "Attribution" or alternatively secure a separate license from
#    Digital Creations.  Digital Creations will not unreasonably
#    deny such a separate license in the event that the request
#    explains in detail a valid reason for withholding attribution.
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
# Attribution
# 
#   Individuals or organizations using this software as a web
#   site ("the web site") must provide attribution by placing
#   the accompanying "button" on the website's main entry
#   point.  By default, the button links to a "credits page"
#   on the Digital Creations' web site. The "credits page" may
#   be copied to "the web site" in order to add other credits,
#   or keep users "on site". In that case, the "button" link
#   may be updated to point to the "on site" "credits page".
#   In cases where this placement of attribution is not
#   feasible, a separate arrangment must be concluded with
#   Digital Creations.  Those using the software for purposes
#   other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.  Where
#   attribution is not possible, or is considered to be
#   onerous for some other reason, a request should be made to
#   Digital Creations to waive this requirement in writing.
#   As stated above, for valid requests, Digital Creations
#   will not unreasonably deny such requests.
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

"""ZServer FTP Channel for use the medusa's ftp server.

FTP Service for Zope.

  This server allows FTP connections to Zope. In general FTP is used
  to manage content. You can:

    * Create and delete Folders, Documents, Files, and Images

    * Edit the contents of Documents, Files, Images

  In the future, FTP may be used to edit object properties.

FTP Protocol

  The FTP protocol for Zope gives Zope objects a way to make themselves
  available to FTP services. See the 'lib/python/OFS/FTPInterface.py' for
  more details.

FTP Permissions

  FTP access is controlled by one permission: 'FTP access' if bound to a
  role, users of that role will be able to list directories, and cd to
  them. Creating and deleting and changing objects are all governed by
  existing Zope permissions.

  Permissions are to a certain extent reflected in the permission bits
  listed in FTP file listings.

FTP Authorization

  Zope supports both normal and anonymous logins. It can be difficult
  to authorize Zope users since they are defined in distributed user
  databases. Normally, all logins will be accepted and then the user must
  proceed to 'cd' to a directory in which they are authorized. In this
  case for the purpose of FTP limits, the user is considered anonymous
  until they cd to an authorized directory.

  Optionally, users can login with a special username which indicates
  where they are defined. Their login will then be authenticated in
  the indicated directory, and they will not be considered anonymous.
  The form of the name is '<username>@<path>' where path takes the form
  '<folder id>[/<folder id>...]' For example: 'amos@Foo/Bar' This will
  authenticate the user 'amos' in the directory '/Foo/Bar'. In addition
  the user's FTP session will be rooted in the authenticated directory,
  i.e. they will not be able to cd out of the directory.

  The main reason to use the rooted FTP login, is to allow non-anonymous
  logins. This may be handy, if for example, you disallow anonymous logins,
  or if you set the limit for simultaneous anonymous logins very low.

"""

from PubCore import handle
from medusa.ftp_server import ftp_channel, ftp_server
from medusa import asyncore, asynchat, filesys
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
    anonymous=1
    
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
        
        # XXX etcetera -- probably set many of these at the start, rather
        #                 than for each request...

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
        
        # handles files as well as directories.
        # XXX also should maybe handle globbing, yuck.
        
        self.push_with_producer(self.get_dir_list (line, 1))
    
    def get_dir_list (self, line, long=0):
        # we need to scan the command line for arguments to '/bin/ls'...
        # XXX clean this up, maybe with getopts
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
        code=response.headers['Status'][:3]
        if code=='200':
            if self.anonymous and not self.userid=='anonymous':
                self.anonymous=None
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
            return  self.make_response(
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
            if self.anonymous and not self.userid=='anonymous':
                self.anonymous=None
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
        code=response.headers['Status'][:3]
        if code=='200':
            self.make_xmit_channel()
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
        i=string.find(self.userid,'@')
        if i ==-1:
            if self.server.limiter.check_limit(self):
                self.respond ('230 Login successful.')
                self.authorized = 1
                self.anonymous = 1
                self.log ('Successful login.')
            else:
                self.respond('421 User limit reached. Closing connection.')
                self.close_when_done()
        else:   
            path=self.userid[i+1:]
            self.userid=self.userid[:i]
            self.anonymous=None
            env=self._get_env()
            path=self._join_paths('/',path,'manage_FTPlist')
            env['PATH_INFO']=path
            outpipe=handle(self.module,env,StringIO())
            self.push_with_producer(ResponseProducer
                    (outpipe,self._cmd_pass,(path[:-15],))) 

    def _cmd_pass(self,path,response):
        code=response.headers['Status'][:3]
        if code=='200':
            if not self.server.limiter.check_limit(self):
                self.close_when_done()
                return self.make_response('421 User limit reached. Closing connection.')    
            listing=marshal.loads(response.content)
            # check to see if we are cding to a non-foldoid object
            if type(listing[0])==type(''):
                return self.make_response('530 Unauthorized.')
            self.path=path or '/'
            self.authorized = 1
            if self.userid=='anonymous':
                self.anonymous=1
            self.log('Successful login.')           
            return self.make_response('230 Login successful.')
        else:
            return  self.make_response('530 Unauthorized.')
        
    
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


class FTPLimiter:
    """Rudimentary FTP limits. Helps prevent denial of service
    attacks. It works by limiting the number of simultaneous
    connections by userid. There are three limits, one for anonymous
    connections, and one for authenticated logins. The total number
    of simultaneous anonymous logins my be less than or equal to the
    anonymous limit. Each authenticated user can have up to the user
    limit number of simultaneous connections. The total limit is the
    maximum number of simultaneous connections of any sort. Do *not*
    set the total limit lower than or equal to the anonymous limit."""
    
    def __init__(self,anon_limit=10,user_limit=4,total_limit=25):
        self.anon_limit=anon_limit
        self.user_limit=user_limit
        self.total_limit=total_limit
    
    def check_limit(self,channel):
        """Check to see if the user has exhausted their limit or not.
        Check for existing channels with the same userid and the same
        ftp server."""
        total=0
        class_total=0
        if channel.anonymous:
            for existing_channel in asyncore.socket_map.keys():
                if (hasattr(existing_channel,'server') and
                        existing_channel.server is channel.server):
                    total=total+1
                    if existing_channel.anonymous:
                        class_total=class_total+1
            if class_total > self.anon_limit:
                return None
        else:                
            for existing_channel in asyncore.socket_map.keys():
                if (hasattr(existing_channel,'server') and
                        existing_channel.server is channel.server):
                    total=total+1
                    if channel.userid==existing_channel.userid:
                        class_total=class_total+1
            if class_total > self.user_limit:
                return None
        if total <= self.total_limit:
            return 1

        
class FTPServer(ftp_server):
    """FTP server for Zope."""
    
    ftp_channel_class = zope_ftp_channel
    limiter=FTPLimiter(10,1)

    def __init__(self,module,*args,**kw):
        apply(ftp_server.__init__, (self, None) + args, kw)
        self.module=module
        
    def handle_accept (self):
        conn, addr = self.accept()
        self.total_sessions.increment()
        print 'Incoming connection from %s:%d' % (addr[0], addr[1])
        self.ftp_channel_class (self, conn, addr, self.module)  


