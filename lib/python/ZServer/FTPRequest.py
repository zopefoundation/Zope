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
"""
FTP Request class for FTP server.

The FTP Request does the dirty work of turning an FTP request into something
that ZPublisher can understand.
"""

from ZPublisher.HTTPRequest import HTTPRequest

from cStringIO import StringIO
import os
from regsub import gsub
from base64 import encodestring
import string

class FTPRequest(HTTPRequest):

    def __init__(self, path, command, channel, response, stdin=None,
                 environ=None):
        if stdin is None: stdin=StringIO()
        if environ is None:
            environ=self._get_env(path, command, channel, stdin)
        self._orig_env=environ
        HTTPRequest.__init__(self, stdin, environ, response, clean=1)
        
        # support for cookies and cookie authentication
        self.cookies=channel.cookies
        if not self.cookies.has_key('__ac') and channel.userid != 'anonymous':
            self.other['__ac_name']=channel.userid
            self.other['__ac_password']=channel.password
        for k,v in self.cookies.items():
            if not self.other.has_key(k):
                self.other[k]=v
        
   
    def retry(self):
        self.retry_count=self.retry_count+1
        r=self.__class__(stdin=self.stdin,
                         environ=self._orig_env,
                         response=self.response.retry(),
                         channel=self, # For my cookies
                         )
        return r
    
    def _get_env(self, path, command, channel, stdin):
        "Returns a CGI style environment"
        env={}
        env['SCRIPT_NAME']='/%s' % channel.module
        env['REQUEST_METHOD']='GET' # XXX what should this be?
        env['SERVER_SOFTWARE']=channel.server.SERVER_IDENT
        if channel.userid != 'anonymous':
            env['HTTP_AUTHORIZATION']='Basic %s' % gsub('\012','',
                    encodestring('%s:%s' % (channel.userid, channel.password)))
        env['SERVER_NAME']=channel.server.hostname
        env['SERVER_PORT']=str(channel.server.port)
        env['REMOTE_ADDR']=channel.client_addr[0]
        env['GATEWAY_INTERFACE']='CGI/1.1' # that's stretching it ;-)
       
        # FTP commands
        #
        if type(command)==type(()):
            args=command[1:]
            command=command[0]
        if command in ('LST','CWD','PASS'):
            env['PATH_INFO']=self._join_paths(channel.path, 
                                              path, 'manage_FTPlist')
        elif command in ('MDTM','SIZE'):
            env['PATH_INFO']=self._join_paths(channel.path, 
                                              path, 'manage_FTPstat')
        elif command=='RETR':
            env['PATH_INFO']=self._join_paths(channel.path, 
                                              path, 'manage_FTPget')
        elif command in ('RMD','DELE'):
            env['PATH_INFO']=self._join_paths(channel.path, 
                                              path, 'manage_delObjects')
            env['QUERY_STRING']='ids=%s' % args[0]
        elif command=='MKD':
            env['PATH_INFO']=self._join_paths(channel.path, 
                                              path, 'manage_addFolder')
            env['QUERY_STRING']='id=%s' % args[0]

        elif command=='RNTO':
            env['PATH_INFO']=self._join_paths(channel.path, 
                                              path, 'manage_renameObject')
            env['QUERY_STRING']='id=%s&new_id=%s' % (args[0],args[1])
            
        elif command=='STOR':
            env['PATH_INFO']=self._join_paths(channel.path, path)
            env['REQUEST_METHOD']='PUT'
            env['CONTENT_LENGTH']=len(stdin.getvalue())
        else:
            env['PATH_INFO']=self._join_paths(channel.path, path, command)
        return env
    
    def _join_paths(self,*args):
        path=apply(os.path.join,args)
        path=os.path.normpath(path)
        if os.sep != '/':
            path=string.replace(path,os.sep,'/')
        return path
        






