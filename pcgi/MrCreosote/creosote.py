#!/usr/bin/env python
# creosote.py - lightweight message passing with datagrams
# JeffBauer@bigfoot.com

import sys, socket

BUFSIZE = 1024
PORT = 7739

def spew(msg, host='localhost', port=PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 0))
    s.sendto(msg, (host, port))

def bucket(port=PORT, logfile=None):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', port))
    print 'creosote bucket waiting on port: %s' % port
    if logfile:
        f = open(logfile, 'a+')
    while 1:
        data, addr = s.recvfrom(BUFSIZE)
        print `data`[1:-1]
        if logfile:
            f.write(`data`[1:-1]+'\n')
            f.flush()

class MrCreosote:
    """lightweight message passing with datagrams"""
    def __init__(self, host='localhost', port=PORT):
        self.host = host
        self.port = port
        self.client = None
        self.disabled = 0
        self.redirect_server = None
        self.redirect_client = None
    def bucket(self, logfile=None):
        bucket(self.port, logfile)
    def redirector(self, host, port=PORT):
        if self.disabled:
            return
        if self.redirect_server == None:
            self.redirect_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.redirect_server.bind(('', self.port))
        if self.redirect_client == None:
            self.redirect_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.redirect_client.bind(('', 0))
        while 1:
            data, addr = self.redirect_server.recvfrom(BUFSIZE)
            self.redirect_client.sendto(data, (host, port))
    def spew(self, msg):
        if self.disabled:
            return
        if self.client == None:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client.bind(('', 0))
        self.client.sendto(msg, (self.host, self.port))

if __name__ == '__main__':
    """usage: creosote [message]"""
    if len(sys.argv) < 2:
        bucket()
    else:
        from string import joinfields
        spew(joinfields(sys.argv[1:],' '))
