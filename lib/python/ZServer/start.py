#!/usr/local/bin/python1.5.1

"""Sample ZServer start script"""

# configuration variables
#
IP_ADDRESS=''
HOST='localhost'
DNS_IP='127.0.0.1'
HTTP_PORT=9673
FTP_PORT=8021
PCGI_PORT=88889
PID_FILE='Zope.pid'
MODULE='Main'
LOG_FILE='ZServer.log'

from medusa import resolver,logger,http_server,asyncore

import zope_handler
import ZServerFTP
import ZServerPCGI

rs = resolver.caching_resolver(DNS_IP)
lg = logger.file_logger(LOG_FILE)

hs = http_server.http_server(
	ip=IP_ADDRESS,
	port=HTTP_PORT,
	resolver=rs,
	logger_object=lg)
	
zh = zope_handler.zope_handler(MODULE,'')
hs.install_handler(zh)

zftp = ZServerFTP.FTPServer(
	module=MODULE,
	hostname=HOST,
	port=FTP_PORT,
	resolver=rs,
	logger_object=lg)

zpcgi = ZServerPCGI.PCGIServer(
	module=MODULE,
	ip=IP_ADDRESS,
	port=PCGI_PORT,
	pid_file=PID_FILE,
	resolver=rs,
	logger_object=lg)

asyncore.loop()


