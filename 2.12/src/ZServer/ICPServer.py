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

# Medusa ICP server
#
# Why would you want to use this?
# see http://www.zope.org/Members/htrd/icp/intro

import sys, string, os, socket, errno, struct

import asyncore

from medusa import counter


ICP_OP_QUERY = 1
ICP_OP_HIT = 2
ICP_OP_MISS = 3
ICP_OP_ERR = 4
ICP_OP_MISS_NOFETCH = 21
ICP_OP_DENIED = 22

class BaseICPServer(asyncore.dispatcher):

    REQUESTS_PER_LOOP = 4
    _shutdown = 0

    def __init__ (self,ip,port):
        asyncore.dispatcher.__init__(self)
        self.ip = ip
        self.port = port
        self.create_socket (socket.AF_INET, socket.SOCK_DGRAM)
        self.set_reuse_addr()
        self.bind((ip,port))
        if ip=='':
            addr = 'any'
        else:
            addr = ip
        self.log_info('ICP server started\n\tAddress: %s\n\tPort: %s' % (addr,port) )

    def clean_shutdown_control(self,phase,time_in_this_phase):
        if phase==1:
            # Stop responding to requests.
            if not self._shutdown:
                self._shutdown = 1
                self.log_info('shutting down ICP')
            if time_in_this_phase<2.0:
                # We have not yet been deaf long enough for our front end proxies to notice.
                # Do not allow shutdown to proceed yet
                return 1
            else:
                # Shutdown can proceed. We dont need a socket any more
                self.close()
                return 0

    def handle_read(self):
        for i in range(self.REQUESTS_PER_LOOP):
            try:
                request, whence = self.socket.recvfrom(16384)
            except socket.error,e:
                if e[0]==errno.EWOULDBLOCK:
                    break
                else:
                    raise
            else:
                if self.check_whence(whence):
                    reply = self.calc_reply(request)
                    if reply:
                        self.socket.sendto(reply,whence)

    def readable(self):
        return not self._shutdown

    def writable(self):
        return 0

    def handle_write (self):
        self.log_info ('unexpected write event', 'warning')

    def handle_error (self):      # don't close the socket on error
        (file,fun,line), t, v, tbinfo = asyncore.compact_traceback()
        self.log_info('Problem in ICP (%s:%s %s)' % (t, v, tbinfo),
                      'error')

    def check_whence(self,whence):
        return 1

    def calc_reply(self,request):
        if len(request)>20:
            opcode,version,length,number,options,opdata,junk = struct.unpack('!BBHIIII',request[:20])
            if version==2:
                if opcode==ICP_OP_QUERY:
                    if len(request)!=length:
                        out_opcode = ICP_OP_ERR
                    else:
                        url = request[24:]
                        if url[-1:]=='\x00':
                            url = url[:-1]
                        out_opcode = self.check_url(url)
                    return struct.pack('!BBHIIII',out_opcode,2,20,number,0,0,0)

    def check_url(self,url):
        # derived classes replace this with a more
        # useful policy
        return ICP_OP_MISS


class ICPServer(BaseICPServer):
    # Products that want to do special ICP handling should .append their hooks into
    # this list. Each hook is called in turn with the URL as a parameter, and
    # they must return an ICP_OP code from above or None. The first
    # non-None return is used as the ICP response
    hooks = []

    def check_url(self,url):
        for hook in self.hooks:
            r = hook(url)
            if r is not None:
                return r
        return ICP_OP_MISS
