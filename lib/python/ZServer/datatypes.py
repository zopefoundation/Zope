##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ZConfig datatype support for ZServer.

Each server type is represented by a ServerFactory instance.
"""

import os
import socket
import ZConfig

_default_host_info = None

def get_default_host_info():
    global _default_host_info
    if _default_host_info is None:
        hostname = socket.gethostname()
        try:
            ip = socket.gethostbyname(hostname)
        except socket.error:
            hostname = 'localhost'
            ip = socket.gethostbyname(hostname)
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except socket.error:
            hostname = ip
        ## AJ: We change 'localhost' to '' to force Medusa to use
        ## any network interface instead of using only 127.0.0.1. This is 
        ## a not totally clean solution :-/ See also Collector #1507.
        if os.name == 'posix' and 'localhost' in hostname.lower(): 
            hostname = ''
        _default_host_info = hostname, ip
    return _default_host_info


class ServerFactory:
    def __init__(self, address=None):
        self.ip = None
        if address is None:
            self.host = None
            self.port = None
        else:
            self.host, self.port = address

    def prepare(self, defaulthost=None, dnsresolver=None,
                module=None, env=None, portbase=None):
        if defaulthost:
            hostname = defaulthost
            ip = socket.gethostbyname(hostname)
        elif defaulthost is '':
            hostname = ''
            ip = '127.0.0.1'
        else:
            hostname, ip = get_default_host_info()
        if not self.host:
            self._set_default_host(hostname, ip)
        else:
            self.ip = socket.gethostbyname(self.host)
        self.dnsresolver = dnsresolver
        self.module = module
        self.cgienv = env
        if portbase and self.port is not None:
            self.port += portbase

    def _set_default_host(self, host, ip):
        self.host = host
        self.ip = ip

    def servertype(self):
        s = self.__class__.__name__
        if s.endswith("Factory"):
            s = s[:-7]
        return s

    def create(self):
        raise NotImplementedError(
            "Concrete ServerFactory classes must implement create().")


class HTTPServerFactory(ServerFactory):
    def __init__(self, section):
        if not section.address:
            raise ZConfig.ConfigurationError(
                "No 'address' settings found "
                "within the 'http-server' or 'webdav-source-server' section")
        ServerFactory.__init__(self, section.address)
        self.force_connection_close = section.force_connection_close
        # webdav-source-server sections won't have webdav_source_clients:
        webdav_clients = getattr(section, "webdav_source_clients", None)
        self.webdav_source_clients = webdav_clients

    def create(self):
        from ZServer import HTTPServer
        from ZServer.AccessLogger import access_logger
        handler = self.createHandler()
        handler._force_connection_close = self.force_connection_close
        if self.webdav_source_clients:
            handler.set_webdav_source_clients(self.webdav_source_clients)
        server = HTTPServer.zhttp_server(ip=self.host, port=self.port,
                                         resolver=self.dnsresolver,
                                         logger_object=access_logger)
        server.install_handler(handler)
        return server

    def createHandler(self):
        from ZServer import HTTPServer
        return HTTPServer.zhttp_handler(self.module, '', self.cgienv)


class WebDAVSourceServerFactory(HTTPServerFactory):
    def createHandler(self):
        from ZServer.WebDAVSrcHandler import WebDAVSrcHandler
        return WebDAVSrcHandler(self.module, '', self.cgienv)


class FTPServerFactory(ServerFactory):
    def __init__(self, section):
        if not section.address:
            raise ZConfig.ConfigurationError(
                "No 'address' settings found within the 'ftp-server' section")
        ServerFactory.__init__(self, section.address)

    def create(self):
        from ZServer.AccessLogger import access_logger
        from ZServer.FTPServer import FTPServer
        return FTPServer(ip=self.host, hostname=self.host, port=self.port,
                         module=self.module, resolver=self.dnsresolver,
                         logger_object=access_logger)


class PCGIServerFactory(ServerFactory):
    def __init__(self, section):
        ServerFactory.__init__(self)
        self.path = section.path

    def create(self):
        from ZServer.AccessLogger import access_logger
        from ZServer.PCGIServer import PCGIServer
        return PCGIServer(ip=self.host, port=self.port,
                          module=self.module, resolver=self.dnsresolver,
                          pcgi_file=self.path,
                          logger_object=access_logger)


class FCGIServerFactory(ServerFactory):
    def __init__(self, section):
        import socket
        if section.address.family == socket.AF_INET:
            address = section.address.address
            path = None
        else:
            address = None
            path = section.address.address
        ServerFactory.__init__(self, address)
        self.path = path

    def _set_default_host(self, host, ip):
        if self.path is None:
            ServerFactory._set_default_host(self, host, ip)

    def create(self):
        from ZServer.AccessLogger import access_logger
        from ZServer.FCGIServer import FCGIServer
        return FCGIServer(ip=self.host, port=self.port,
                          socket_file=self.path,
                          module=self.module, resolver=self.dnsresolver,
                          logger_object=access_logger)


class MonitorServerFactory(ServerFactory):
    def __init__(self, section):
        ServerFactory.__init__(self, section.address)

    def create(self):
        password = self.getPassword()
        if password is None:
            msg = ('Monitor server not started because no emergency user '
                   'exists.')
            import zLOG
            zLOG.LOG("Zope", zLOG.ERROR, msg)
            return
        from ZServer.medusa.monitor import secure_monitor_server
        return secure_monitor_server(hostname=self.host, port=self.port,
                                     password=password)

    def getPassword(self):
        # XXX This is really out of place; there should be a better
        # way.  For now, at least we can make it a separate method.

        import ZODB # :-( required to import user
        from AccessControl.User import emergency_user
        if hasattr(emergency_user, '__null_user__'):
            pw = None
        else:
            pw = emergency_user._getPassword()
        return pw


class ICPServerFactory(ServerFactory):
    def __init__(self, section):
        ServerFactory.__init__(self, section.address)

    def create(self):
        from ZServer.ICPServer import ICPServer
        return ICPServer(self.ip, self.port)
