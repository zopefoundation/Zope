#!/usr/local/bin/python1.5.1

"""Sample ZServer start script"""

import sys
import os

# configuration variables
#
IP_ADDRESS=''
HOST='tarzan.digicool.com'
DNS_IP='206.156.192.156'
HTTP_PORT=9673
FTP_PORT=8021
MODULE='Main'
ZOPE_HOME='/projects/users/amos/ftpbox/Zope--linux2-x86'


sys.path.insert(0,os.path.join(ZOPE_HOME,'lib/python'))

from medusa import resolver,logger,http_server,asyncore

import zope_handler
import ZServerFTP

lg = logger.file_logger (sys.stdout)

rs = resolver.caching_resolver(DNS_IP)

hs = http_server.http_server (IP_ADDRESS, HTTP_PORT, rs, lg)
zh = zope_handler.zope_handler(MODULE)
hs.install_handler(zh)

zftp = ZServerFTP.zope_ftp_server(
	MODULE,
	hostname=HOST,
	port=FTP_PORT,
	resolver=rs,
	logger_object=lg)

asyncore.loop()

