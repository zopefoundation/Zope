##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
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
from base64 import encodestring
import re

class FTPRequest(HTTPRequest):

    def __init__(self, path, command, channel, response, stdin=None,
                 environ=None, globbing=None, recursive=0, size=None):

        # we need to store the globbing information to pass it
        # to the ZPublisher and the manage_FTPlist function
        # (ajung)
        self.globbing = globbing
        self.recursive= recursive

        if stdin is None:
            size = 0
            stdin = StringIO()

        if environ is None:
            environ = self._get_env(path, command, channel, stdin, size)

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

    def _get_env(self, path, command, channel, stdin, size):
        "Returns a CGI style environment"
        env={}
        env['SCRIPT_NAME']='/%s' % channel.module
        env['REQUEST_METHOD']='GET' # XXX what should this be?
        env['SERVER_SOFTWARE']=channel.server.SERVER_IDENT
        if channel.userid != 'anonymous':
            env['HTTP_AUTHORIZATION']='Basic %s' % re.sub('\012','',
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

        elif command=='RNFR':
            env['PATH_INFO']=self._join_paths(channel.path,
                                              path, 'manage_hasId')
            env['QUERY_STRING']='id=%s' % (args[0])

        elif command=='RNTO':
            env['PATH_INFO']=self._join_paths(channel.path,
                                              path, 'manage_renameObject')
            env['QUERY_STRING']='id=%s&new_id=%s' % (args[0],args[1])

        elif command=='STOR':
            env['PATH_INFO'] = self._join_paths(channel.path, path)
            env['REQUEST_METHOD'] = 'PUT'
            env['CONTENT_LENGTH'] = long(size)

        else:
            env['PATH_INFO']=self._join_paths(channel.path, path, command)

        # Fake in globbing information
        env['GLOBBING'] = self.globbing
        env['FTP_RECURSIVE'] = self.recursive

        return env

    def _join_paths(self,*args):
        path=apply(os.path.join,args)
        path=os.path.normpath(path)
        if os.sep != '/':
            path=path.replace(os.sep,'/')
        return path
