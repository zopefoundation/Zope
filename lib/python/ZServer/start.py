#!/usr/local/bin/python1.5.1
"""ZServer start script

This start script configures ZServer.

XXX comment this script much more to explain
    what the different config option are.

"""
# Zope configuration
#
SOFTWARE_HOME='d:\\program files\\1.10.2'
import sys,os
sys.path.insert(0,os.path.join(SOFTWARE_HOME,'lib','python'))

# ZServer configuration 
#
IP_ADDRESS=''
HOST='localhost'
DNS_IP='205.240.25.3'
HTTP_PORT=9673
FTP_PORT=8021
PCGI_PORT=88889
PID_FILE=os.path.join(SOFTWARE_HOME,'var','ZServer.pid')
LOG_FILE=os.path.join(SOFTWARE_HOME,'var','ZServer.log')
MODULE='Main'


from medusa import resolver,logger,http_server,asyncore
from HTTPServer import zhttp_server, zhttp_handler
from PCGIServer import PCGIServer
from FTPServer import FTPServer

rs = resolver.caching_resolver(DNS_IP)
lg = logger.file_logger(LOG_FILE)

hs = zhttp_server(
	ip=IP_ADDRESS,
	port=HTTP_PORT,
	resolver=rs,
	logger_object=lg)

zh = zhttp_handler(MODULE,'')
hs.install_handler(zh)

zpcgi = PCGIServer(
	module=MODULE,
	ip=IP_ADDRESS,
	port=PCGI_PORT,
	pid_file=PID_FILE,
	resolver=rs,
	logger_object=lg)
	
zftp = FTPServer(
	module=MODULE,
	hostname=HOST,
	port=FTP_PORT,
	resolver=rs,
	logger_object=lg)


asyncore.loop()


