
import sys
import socket
import select

print "Simulating Unix-domain logging using file: %s" % sys.argv[1]

log_socket = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
log_socket.bind( sys.argv[1] )

while 1:
   n = select.select( [ log_socket ], [], [] )
   print ".",
   if n > 0:
      print log_socket.recv( 1024 )
