# PCGIPublisher.py
# Persistent CGI Publisher - jeffbauer@bigfoot.com
#
# Copyright (c) 1998, Digital Creations, Fredericksburg, VA, USA.  All
# rights reserved. This software includes contributions from Jeff Bauer.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#   o Redistributions of source code must retain the above copyright
#     notice, this list of conditions, and the disclaimer that follows.
#
#   o Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions, and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#
#   o All advertising materials mentioning features or use of this
#     software must display the following acknowledgement:
#
#       This product includes software developed by Digital Creations
#       and its contributors.
#
#   o Neither the name of Digital Creations nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS *AS IS* AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# 2.0 alpha4:
#   - adds NT support, using INET sockets
#   - added Mike Fletcher's Microsoft IIS hack, suggested by Amos Latteier
#
# 2.0 alpha3:
#   - adds error checking
#   - expands header to 10 bytes (extra byte defines an out-of-band msg)
#
# 2.0 alpha1:
#   - add support for new PCGI_ directives
#   - re-write module as a class, rather than a set of functions

__version__ = "2.0a4"

class PCGIPublisher:
    def __init__(self, resource=None):
        ### resources passed from the environment, info file or pcgi-wrapper
        self.errorLogFile = None
        self.hostname = None
        self.port = 0
        self.insertPath = None
        self.moduleName = None
        self.modulePath = None
        self.socketFile = None
        self.pidFile = None
        self.swhome = None
        self.sock = None

        ### bound imports ###
        self.StringIO = None
        self.publish_module = None

        ### other ###
        self.bufsize = 8192
        self.error = 0

        if resource is None:
            self.getResources()
        else:
            self.resource = resource
        self.initPCGI()

    def cleanup(self):
        if self.socketFile:
            import os
            if os.path.exists(self.socketFile): 
                try:
                    os.unlink(self.socketFile)
                except os.error:
                    pass

    def getResources(self):
        """
        Obtain the publisher resources from the environment.  Done here
        in a separate method to make it easy to override, because we may
        not always and forever obtain our resources from the environment.
        """
        import os
        self.resource = os.environ

    def fatalError(self, errmsg=''):
        if self.errorLogFile:
            import sys, traceback, StringIO
            try:
                from time import asctime, localtime, time
                timeStamp = asctime(localtime(time()))
            except ImportError:
                timeStamp = '???'
            try:
                f = open(self.errorLogFile, 'a+')
                f.write("%s  %s\n" % (timeStamp, errmsg))
                if sys.exc_type != SystemExit:
                    trace=StringIO.StringIO()
                    traceback.print_exception(sys.exc_type,
                                              sys.exc_value,
                                              sys.exc_traceback,
                                              None,
                                              trace)
                    f.write("  %s\n" % trace.getvalue())
                f.close()
            except IOError:
                pass
        self.cleanup()
        self.error = 1

    def initPCGI(self):
        import os
        self.initPrincipia()
        if self.resource.has_key('PCGI_ERROR_LOG'):
            self.errorLogFile = self.resource['PCGI_ERROR_LOG']
        if self.resource.has_key('PCGI_HOST'):
            self.hostname = self.resource['PCGI_HOST']
        if self.resource.has_key('PCGI_INSERT_PATH'):
            self.insertPath = self.resource['PCGI_INSERT_PATH']
        if self.resource.has_key('PCGI_MODULE_PATH'):
            self.modulePath = self.resource['PCGI_MODULE_PATH']
        if self.resource.has_key('PCGI_NAME'):
            self.moduleName = self.resource['PCGI_NAME']
        if self.resource.has_key('PCGI_PID_FILE'):
            self.pidFile = self.resource['PCGI_PID_FILE']
        if self.resource.has_key('PCGI_PORT'):
            import string
            try: self.port = string.atoi(self.resource['PCGI_PORT'])
            except ValueError: pass
        if self.resource.has_key('PCGI_SOCKET_FILE'):
            self.socketFile = self.resource['PCGI_SOCKET_FILE']
        self.insertSysPath()

        if not self.moduleName:
            return self.fatalError("missing module name, try specifying PCGI_NAME")

        ### TODO: probably should make an attempt to import self.moduleName
        ### to provide the user with earliest possible response.

        try:
            from cStringIO import StringIO
        except:
            from StringIO import StringIO
        self.StringIO = StringIO

        try:
            from ZPublisher import publish_module
        except ImportError:
            try:
                from cgi_module_publisher import publish_module
            except ImportError:
                return self.fatalError(
                    "unable to import publish_module from ZPublisher")

        self.publish_module = publish_module

        if not self.pidFile:
            return self.fatalError("missing pid file")

        ### create pid file ###
        try:
            f = open(self.pidFile, 'wb')
            f.write(str(os.getpid()))
            f.close()
        except IOError:
            return self.fatalError("unable to write to pid file: %s" % self.pidFile)
        import socket
        if not self.socketFile:
            return self.fatalError("missing socket file")
        if self.port:
            if os.sep == '/':
                return self.fatalError("INET sockets not yet available on Unix")
            if self.hostname is None:
                self.hostname = socket.gethostname()
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.bind(self.hostname, self.port)
            except socket.error:
                return self.fatalError("error binding to socket: %s" % self.socketFile)
            try:
                sf = open(self.socketFile, 'wb')
                sf.write("%s\n%s\n" % (self.hostname, self.port))
                sf.close()
            except IOError:
                return self.fatalError("error attempting to write socket file: %s" % self.socketFile)
        else:
            try: os.unlink(self.socketFile)
            except os.error: pass
            try:
                self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.sock.bind(self.socketFile)
            except socket.error:
                return self.fatalError("error binding to socket: %s" % self.socketFile)
            try: os.chmod(self.socketFile, 0777)
            except os.error: pass

    def initPrincipia(self):
        if self.resource.has_key('SOFTWARE_NAME'):
            self.moduleName = self.resource['SOFTWARE_NAME']

    def insertSysPath(self, insertPath=None):
        import os, sys, string
        if insertPath is None: 
            insertPath = self.insertPath
        if insertPath:
            sys.path[0:0]=string.split(insertPath,':')
        elif self.resource.has_key('PCGI_WORKING_DIR'):
            ### Note: PCGI_WORKING_DIR is a deprecated pcgi directive ###
            workDir = self.resource['PCGI_WORKING_DIR']
            while workDir[-1:]=='/' or workDir[-1:]=='\\':
                workDir=workDir[:-1]
            sys.path[0:0]=[workDir]
        else:
            pass

        # The present assumption is that if the module path isn't in
        # sys.path, we want it put there, even if the PCGI_INSERT_PATH 
        # directive has been specified.
        if self.modulePath:
            d, s = os.path.split(self.modulePath)
            if not d in sys.path:
                sys.path[0:0] = [d]
            # If the moduleName is not known at this time, we make a
            # reasonable guess based on the path.  It might behoove the
            # user to explicitly specify PCGI_NAME, however.
            if not self.moduleName:
                import string
                self.moduleName = string.splitfields(s,'.')[0]

    def handler(self, conn):
        from string import split, join, atoi
        hdr = conn.recv(10)

        size = atoi(hdr)
        buff = []
        while size > 0:
            data = conn.recv(size)
            size = size - len(data)
            buff.append(data)

        ### XXX - Later: add out-of-band data handling ###
        if (hdr[0] != '0'):
            return

        env = {}
        for i in filter(None, split(join(buff,''),'\000')):
            e = split(i,'=')
            if len(e) > 2:
                env[e[0]] = join(e[1:],'=')
            else:
                env[e[0]] = e[1]
        size = atoi(conn.recv(10))
        if size > 1048576:
            ### write large upload data to a file ###
            from tempfile import TemporaryFile
            stdin = TemporaryFile('w+b')
            bufsize = self.bufsize
            while size > 0:
                if size < bufsize: 
                    bufsize=size
                data = conn.recv(bufsize)
                size = size - len(data)
                stdin.write(data)
            stdin.seek(0,0)
        else:
            ### use StringIO for smaller data ###
            buff = []
            while size > 0:
                data = conn.recv(size)
                size = size-len(data)
                buff.append(data)
            stdin = self.StringIO(join(buff,''))
        stdout = self.StringIO()
        stderr = self.StringIO()

        ### IIS hack to fix broken PATH_INFO
        ### taken from Mike Fletcher's win_cgi_module_publisher
        import string
        if env.has_key('SERVER_SOFTWARE') and string.find(env['SERVER_SOFTWARE'],'Microsoft-IIS') != -1:
            script = filter(None,string.split(string.strip(env['SCRIPT_NAME']),'/'))
            path = filter(None,string.split(string.strip(env['PATH_INFO']),'/'))
            env['PATH_INFO'] = string.join(path[len(script):],'/')

        try:
            self.publish_module(self.moduleName,stdin=stdin,stdout=stdout,stderr=stderr,environ=env)
        except:
            self.fatalError("unable to publish module")

        stdin.close()
        stdout=stdout.getvalue()
        stderr=stderr.getvalue()
        conn.send('%010d' % len(stdout))
        if len(stdout) > 0:
            conn.send(stdout)
        conn.send('%010d' % len(stderr))
        if len(stderr) > 0:
            conn.send(stderr)
        conn.close()

    def listen(self):
        """
        Note to sub-classes:  Aside from the constructor, listen() should 
        be the only method you *must* invoke.
        """
        if self.error:
            return self.fatalError("attempt to listen after fatal error")

        import os, sys
        if not self.sock:
            return self.fatalError("no socket available")

        self.sock.listen(512)
        try: sys.stderr.close()
        except: pass

        while not self.error:
            conn, accept = self.sock.accept()
            try:
                self.handler(conn)
            except socket.error:
                pass

def main():
    try:
        import os, sys, string, traceback
        pcgiPublisher = PCGIPublisher(os.environ)
        if not pcgiPublisher.error:
            pcgiPublisher.listen()
    except ImportError:
        print "Content-type: text/html"
        print
        print "PCGIPublisher catastrophic import error"

if __name__ == '__main__':
    try: 
        main()
    finally:
        import os
        if os.environ.has_key('PCGI_SOCKET_FILE'):
            try: os.unlink(os.environ['PCGI_SOCKET_FILE'])
            except os.error: pass
