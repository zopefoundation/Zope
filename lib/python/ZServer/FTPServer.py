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
from medusa.ftp_server import ftp_channel, ftp_server, recv_channel
from medusa import asyncore, asynchat, filesys
from FTPResponse import make_response
from FTPRequest import FTPRequest

from ZServer import CONNECTION_LIMIT

from cStringIO import StringIO
import string
import os
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
        self.cookies={}
    
    def _join_paths(self,*args):
        path=apply(os.path.join,args)
        path=os.path.normpath(path)
        if os.sep != '/':
            path=string.replace(path,os.sep,'/')
        return path
    
    # Overriden async_chat methods

    def push(self, producer, send=1):
        # this is thread-safe when send is false
        # note, that strings are not wrapped in 
        # producers by default
        self.producer_fifo.push(producer)
        if send: self.initiate_send()
        
    push_with_producer=push
    
    
    # Overriden ftp_channel methods

    def cmd_nlst (self, line):
        'give name list of files in directory'
        self.get_dir_list(line,0)

    def cmd_list (self, line):
        'give list files in a directory'
        
        # handles files as well as directories.
        # XXX also should maybe handle globbing, yuck.
  
        self.get_dir_list(line,1)
    
    def get_dir_list(self, line, long=0):
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
        self.listdir(dir, long)
    
    def listdir (self, path, long=0):
        response=make_response(self, self.listdir_completion, long)
        request=FTPRequest(path, 'LST', self, response)
        handle(self.module, request, response)         
        
    def listdir_completion(self, long, response):
        status=response.getStatus()
        if status==200:
            if self.anonymous and not self.userid=='anonymous':
                self.anonymous=None
            dir_list=''
            file_infos=response._marshalledBody()
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
            self.respond(
                '150 Opening %s mode data connection for file list' % (
                    self.type_map[self.current_mode]
                    )
                )   
        elif status==401:
            self.respond('530 Unauthorized.')
        else:
            self.respond('550 Could not list directory.')

    def cmd_cwd (self, line):
        'change working directory'
        response=make_response(self, self.cwd_completion, 
                self._join_paths(self.path,line[1]))
        request=FTPRequest(line[1],'CWD',self,response)
        handle(self.module,request,response)       

    def cwd_completion(self,path,response):
        'cwd completion callback'
        status=response.getStatus()
        if status==200:
            listing=response._marshalledBody()
            # check to see if we are cding to a non-foldoid object
            if type(listing[0])==type(''):
                self.respond('550 No such directory.')
                return
            else:
                self.path=path or '/'
                self.respond('250 CWD command successful.')
                # now that we've sucussfully cd'd perhaps we are no
                # longer anonymous
                if self.anonymous and not self.userid=='anonymous':
                    self.anonymous=None
        elif status==401:
            self.respond('530 Unauthorized.')
        else:
            self.respond('550 No such directory.')

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
    
    def cmd_mdtm(self, line):
        'show last modification time of file'
        if len (line) != 2:
            self.command.not_understood (string.join (line))
            return
        response=make_response(self, self.mdtm_completion)
        request=FTPRequest(line[1],'MDTM',self,response)
        handle(self.module,request,response)       
    
    def mdtm_completion(self, response):
        status=response.getStatus()
        if status==200:
            mtime=response._marshalledBody()[stat.ST_MTIME]
            mtime=time.gmtime(mtime)
            self.respond('213 %4d%02d%02d%02d%02d%02d' % (
                                mtime[0],
                                mtime[1],
                                mtime[2],
                                mtime[3],
                                mtime[4],
                                mtime[5]
                                ))
        elif status==401:
            self.respond('530 Unauthorized.') 
        else:
            self.respond('550 Error getting file modification time.')  
                
    def cmd_size(self, line):
        'return size of file'
        if len (line) != 2:
            self.command.not_understood (string.join (line))
            return
        response=make_response(self, self.size_completion)
        request=FTPRequest(line[1],'SIZE',self,response)
        handle(self.module,request,response)       
        
    def size_completion(self,response):
        status=response.getStatus()
        if status==200:
            self.respond('213 %d'% response._marshalledBody()[stat.ST_SIZE])
        elif status==401:
            self.respond('530 Unauthorized.') 
        else:
            self.respond('550 Error getting file size.')   
            
            #self.client_dc.close_when_done()

    def cmd_retr(self,line):
        if len(line) < 2:
            self.command_not_understood (string.join (line))
            return
        response=make_response(self, self.retr_completion, line[1])
        self._response_producers = response.stdout._producers
        request=FTPRequest(line[1],'RETR',self,response)
        handle(self.module,request,response) 

    def retr_completion(self, file, response):        
        status=response.getStatus()
        if status==200:
            self.make_xmit_channel()
            if not response._wrote:
                self.client_dc.push(response.body)
            else:
                for producer in self._response_producers:
                    self.client_dc.push_with_producer(producer)
            self._response_producers = None
            self.client_dc.close_when_done()
            self.respond(
                    "150 Opening %s mode data connection for file '%s'" % (
                        self.type_map[self.current_mode],
                        file
                        ))
        elif status==401:
            self.respond('530 Unauthorized.')
        else:
            self.respond('550 Error opening file.')    

    def cmd_stor (self, line, mode='wb'):
        'store a file'
        if len (line) < 2:
            self.command_not_understood (string.join (line))
            return
        elif self.restart_position:
            restart_position = 0
            self.respond ('553 restart on STOR not yet supported')
            return
            
        # XXX Check for possible problems first?
        #     Right now we are limited in the errors we can issue, since
        #     we agree to accept the file before checking authorization
        
        fd=ContentReceiver(self.stor_callback, line[1])
        self.respond (
            '150 Opening %s connection for %s' % (
                self.type_map[self.current_mode],
                line[1]
                )
            )
        self.make_recv_channel(fd)
    
    def stor_callback(self,path,data):
        'callback to do the STOR, after we have the input'
        response=make_response(self, self.stor_completion)
        request=FTPRequest(path,'STOR',self,response,stdin=data)
        handle(self.module,request,response)       
           
    def stor_completion(self,response):
        status=response.getStatus()        
        if status in (200,201,204,302):
            self.client_dc.channel.respond('226 Transfer complete.')
        elif status==401:
            self.client_dc.channel.respond('426 Unauthorized.')
        else:
            self.client_dc.channel.respond('426 Error creating file.')       
        self.client_dc.close()
        
    def cmd_dele(self, line):
        if len (line) != 2:
            self.command.not_understood (string.join (line))
            return
        path,id=os.path.split(line[1])
        response=make_response(self, self.dele_completion)
        request=FTPRequest(path,('DELE',id),self,response)
        handle(self.module,request,response)       
        
    def dele_completion(self,response):   
        status=response.getStatus()
        if status==200 and string.find(response.body,'Not Deletable')==-1:
            self.respond('250 DELE command successful.')
        elif status==401:
            self.respond('530 Unauthorized.') 
        else:
            self.respond('550 Error deleting file.')       

    def cmd_mkd(self, line):
        if len (line) != 2:
            self.command.not_understood (string.join (line))
            return
        path,id=os.path.split(line[1])
        response=make_response(self, self.mkd_completion)
        request=FTPRequest(path,('MKD',id),self,response)
        handle(self.module,request,response)       
    
    cmd_xmkd=cmd_mkd
    
    def mkd_completion(self,response):
        status=response.getStatus()
        if status==200:
            self.respond('257 MKD command successful.')
        elif status==401:
            self.respond('530 Unauthorized.')
        else:
            self.respond('550 Error creating directory.')

    def cmd_rmd(self, line):
        # XXX should object be checked to see if it's folderish
        #     before we allow it to be RMD'd?
        if len (line) != 2:
            self.command.not_understood (string.join (line))
            return
        path,id=os.path.split(line[1])
        response=make_response(self, self.rmd_completion)
        request=FTPRequest(path,('RMD',id),self,response)
        handle(self.module,request,response)       
        
    cmd_xrmd=cmd_rmd

    def rmd_completion(self,response):
        status=response.getStatus()
        if status==200 and string.find(response.body,'Not Deletable')==-1:
            self.respond('250 RMD command successful.')
        elif status==401:
            self.respond('530 Unauthorized.') 
        else:
            self.respond('550 Error removing directory.')          

    def cmd_user(self, line):
        'specify user name'
        if len(line) > 1:
            self.userid = line[1]
            self.respond('331 Password required.')
        else:
            self.command_not_understood (string.join (line))

    def cmd_pass(self, line):
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
                self.log_info ('Successful login.')
            else:
                self.respond('421 User limit reached. Closing connection.')
                self.close_when_done()
        else:   
            path=self.userid[i+1:]
            self.userid=self.userid[:i]
            self.anonymous=None
            response=make_response(self, self.pass_completion,
                    self._join_paths('/',path))
            request=FTPRequest(path,'PASS',self,response)
            handle(self.module,request,response) 


    def pass_completion(self,path,response):
        status=response.getStatus()
        if status==200:
            if not self.server.limiter.check_limit(self):
                self.close_when_done()
                self.respond('421 User limit reached. Closing connection.')    
                return
            listing=response._marshalledBody()
            # check to see if we are cding to a non-foldoid object
            if type(listing[0])==type(''):
                self.respond('530 Unauthorized.')
                return
            self.path=path or '/'
            self.authorized = 1
            if self.userid=='anonymous':
                self.anonymous=1
            self.log_info('Successful login.')           
            self.respond('230 Login successful.')
        else:
            self.respond('530 Unauthorized.')
        
    def cmd_appe(self, line):
        self.respond('502 Command not implemented.')


# Override ftp server receive channel reponse mechanism 
# XXX hack alert, this should probably be redone in a more OO way.

def handle_close (self):
    """response and closure of channel is delayed."""
    s = self.channel.server
    s.total_files_in.increment()
    s.total_bytes_in.increment(self.bytes_in.as_long())
    self.fd.close()
    self.readable=lambda :0 # don't call close again

recv_channel.handle_close=handle_close

  
class ContentReceiver:
    "Write-only file object used to receive data from FTP"
    
    def __init__(self,callback,*args):
        self.data=StringIO()
        self.callback=callback
        self.args=args
        
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
            for existing_channel in asyncore.socket_map.values():
                if (hasattr(existing_channel,'server') and
                        existing_channel.server is channel.server):
                    total=total+1
                    if existing_channel.anonymous:
                        class_total=class_total+1
            if class_total > self.anon_limit:
                return None
        else:                
            for existing_channel in asyncore.socket_map.values():
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
        self.log_info('Incoming connection from %s:%d' % (addr[0], addr[1]))
        self.ftp_channel_class (self, conn, addr, self.module)  

    def readable(self):
        return len(asyncore.socket_map) < CONNECTION_LIMIT

    def listen(self, num):
        # override asyncore limits for nt's listen queue size
        self.accepting = 1
        return self.socket.listen (num)
