"""Sample ZServer start script"""

import sys
from medusa import resolver
from medusa import logger
from medusa import http_server
from medusa import asyncore
import zope_handler

IP_ADDRESS='127.0.0.1'
HTTP_PORT=9673
MODULE='Main'

lg = logger.file_logger (sys.stdout)
rs = resolver.caching_resolver ('127.0.0.1')
hs = http_server.http_server (IP_ADDRESS, HTTP_PORT, rs, lg)
zh = zope_handler.zope_handler(MODULE)
hs.install_handler(zh)
hs.debug=1


asyncore.loop()

