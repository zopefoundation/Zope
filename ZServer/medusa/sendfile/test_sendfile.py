# -*- Mode: Python; tab-width: 4 -*-

RCS_ID = '$Id: test_sendfile.py,v 1.3 2001/05/01 11:45:27 andreas Exp $'

import asyncore
import os
import socket
import string

# server: just run the script with no args
# client: python test_sendfile.py -c <remote-host> <remote-filename>

if __name__ == '__main__':
    import sys
    if '-c' in sys.argv:
        import operator
        import socket
        s = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
        host = sys.argv[2]
        s.connect ((host, 9009))
        fname = sys.argv[3]
        s.send (fname + '\r\n')
        size = string.atoi (s.recv(8), 16)
        total = 0
        blocks = []
        while (total < size):
            block = s.recv (8192)
            if not block:
                break
            else:
                total = total + len(block)
                blocks.append (block)
        import sys
        for b in blocks:
            sys.stdout.write (b)
    else:
        import asynchat_sendfile
        
        class test_channel (asynchat_sendfile.async_chat_with_sendfile):
        
            def __init__ (self, conn, addr):
                asynchat_sendfile.async_chat_with_sendfile.__init__ (self, conn)
                self.set_terminator ('\r\n')
                self.buffer = ''
                
            def collect_incoming_data (self, data):
                self.buffer = self.buffer + data
                
            def found_terminator (self):
                filename, self.buffer = self.buffer, ''
                if filename:
                    fd = os.open (filename, os.O_RDONLY, 0644)
                    size = os.lseek (fd, 0, 2)
                    os.lseek (fd, 0, 0)
                    self.push ('%08x' % size)
                    self.push_sendfile (fd, 0, size, self.sendfile_callback)
                    self.close_when_done()
                else:
                    self.push ('ok, bye\r\n')
                    self.close_when_done()
                    
            def sendfile_callback (self, success, fd):
                os.close (fd)
                
        class test_server (asyncore.dispatcher):
            def __init__ (self, addr=('', 9009)):
                self.create_socket (socket.AF_INET, socket.SOCK_STREAM)
                self.set_reuse_addr()
                self.bind (addr)
                self.listen (2048)
                print 'server started on', addr
                
            def handle_accept (self):
                conn, addr = self.accept()
                test_channel (conn, addr)
                
        test_server()
        asyncore.loop()
