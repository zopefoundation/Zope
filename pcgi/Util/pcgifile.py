#!/usr/local/bin/python
# pcgifile.py - pcgi info file sanity testing - jeffbauer@bigfoot.com
# Copyright(c) 1998, Jeff Bauer

# 0.6a  August 9, 1998
#   - added socket checking
#
# 0.5a  August 7, 1998
#   - added NT compatibility
#   - improved import checking
#
# 0.4a  July 27, 1998
#   - added checks for executable permissions
#   - print versions of relevant modules

__version__ = "0.6a"
Delimiter = '='

# no class-based exceptions due to 1.4 compatbility
PcgiFileException='PcgiFileException'

class PcgiFile:
    def __init__(self, pcgifile):
        self.pcgifile = pcgifile
        self.infodict = {}
        self.combined = {}
        self.log = []
        self.resource = []
        self.file_contents = []
        self.module_version = []
        self.continue_testing = 1
        self.pcgi_wrapper = None
        try:
            self.readInfoFile()
            self.checkRequiredKeys()
            self.checkPCGIValues()
            self.lookupPCGIPublisher()
            self.checkWritePermissions()
            self.checkImports()
            self.checkSockets()
        except PcgiFileException:
            self.continue_testing = 0

    def checkImports(self):
        try:
            from cgi_module_publisher import publish_module
        except ImportError:
            self.log.append("error attempting: 'from cgi_module_publisher import publish_module'")
            raise PcgiFileException

        try:
            import cgi_module_publisher, CGIResponse
            self.module_version.append("%-20s %-7s  %s" % \
                                       ('cgi_module_publisher',
                                        cgi_module_publisher.__version__,
                                        cgi_module_publisher.__file__) )
            self.module_version.append("%-20s %-7s  %s" % \
                                       ('CGIResponse',
                                        CGIResponse.__version__,
                                        CGIResponse.__file__) )
            self.module_version.append("%-20s %-7s  %s" %
                                       ('pcgifile',
                                        __version__,
                                        sys.argv[0]) )
            self.module_version.append("%-20s %-7s  %s" % \
                                       ('pcgi-wrapper',
                                        self.getPcgiWrapperVersion(),
                                        self.pcgi_wrapper))
        except ImportError:
            pass
        except NameError:
            pass

        try:
            import pcgi_publisher
        except ImportError:
            if self.combined.has_key('PCGI_PUBLISHER'):
                d, s = os.path.split(self.combined['PCGI_PUBLISHER'])
                if not d in sys.path:
                    sys.path.append(d)
        try:
            import pcgi_publisher
            self.module_version.append("%-20s %-7s  %s" % \
                                       ('pcgi_publisher',
                                        pcgi_publisher.__version__,
                                        pcgi_publisher.__file__))
        except ImportError:
            pass
        except NameError:
            pass

    def checkPCGIValues(self):
        if self.combined.has_key('PCGI_EXE'):
            sw_exe = self.combined['PCGI_EXE']
        else:
            sw_exe = sys.executable
            self.log.append("advisory recommendation: specify PCGI_EXE=%s" % \
                            sys.executable)
        if os.path.isfile(sw_exe):
            self.resource.append("Executable:\t%s" % sw_exe)
        else:
            self.log.append("executable not found: %s" % sw_exe)
            raise PcgiFileException
        if self.combined.has_key('PCGI_PID_FILE'):
            f = self.combined['PCGI_PID_FILE']
            d = os.path.split(f)[0]
            if os.path.isdir(d):
                self.resource.append("PID file:\t%s" % f)
            else:
                self.log.append("directory not found: %s" % d)
                raise PcgiFileException
        if self.combined.has_key('PCGI_SOCKET_FILE'):
            f = self.combined['PCGI_SOCKET_FILE']
            d = os.path.split(f)[0]
            if os.path.isdir(d):
                self.resource.append("Socket file:\t%s" % f)
            else:
                self.log.append("directory not found: %s" % d)
                raise PcgiFileException
        if not self.combined.has_key('PCGI_NAME'):
            self.log.append("advisory recommendation: specify PCGI_NAME")
        if self.combined.has_key('PCGI_MODULE_PATH'):
            p = self.combined['PCGI_MODULE_PATH']
            if os.path.isfile(p):
                self.resource.append("Module:\t%s" % p)
            else:
                self.log.append("module not found: %s" % p)
                raise PcgiFileException
        if self.combined.has_key('PCGI_ERROR_LOG'):
            self.resource.append("Error Log:\t%s" % \
                                 self.combined['PCGI_ERROR_LOG'])
        if self.combined.has_key('PCGI_WORKING_DIR'): # deprecated
            d = self.combined['PCGI_WORKING_DIR']
            if os.path.isfile(d):
                self.resource.append("Working Directory:\t%s" % d)
            else:
                self.log.append("working directory not found: %s" % d)
                raise PcgiFileException

    def checkRequiredKeys(self):
        """
        Check for the required PCGI keys.
        """
        for (k,v) in os.environ.items():
            self.combined[k] = v
        for (k,v) in self.infodict.items():
            if self.combined.has_key(k):
                self.log.append("%s=%s, overwrites: %s" % (k, v, self.combined[k]))
            self.combined[k] = v
        for k in ['PCGI_PID_FILE','PCGI_SOCKET_FILE','PCGI_MODULE_PATH']:
            if not self.combined.has_key(k):
                self.log.append("missing parameter: %s" % k)
                raise PcgiFileException
        # PCGI_INFO_FILE is assigned by the pcgi-wrapper, so that it
        # may be known (made available) to pcgi_publisher.
        self.combined['PCGI_INFO_FILE'] = self.pcgifile

    def checkSockets(self):
        """
        Check for possible socket-related error conditions.
        """
        try:
            import socket
        except ImportError:
            self.log.append("unable to import socket module")
            raise PcgiFileException

        port = None
        if self.combined.has_key('PCGI_PORT'):
            try:
                port = string.atoi(self.combined['PCGI_PORT'])
            except ValueError:
                self.log.append("invalid port '%s', PCGI_PORT must be an integer" % self.combined['PCGI_PORT'])
                raise PcgiFileException
        if os.name == 'posix':
            if port:
                self.log.append("cannot specify PCGI_PORT directive on Unix - no support for INET sockets")
                raise PcgiFileException
        elif not port:
            self.log.append("win32 platform must specify missing PCGI_PORT directive (default=7244)");
            raise PcgiFileException

        if port:
            if self.combined.has_key('PCGI_HOST'):
                hostname = self.combined['PCGI_HOST']
                if hostname != socket.gethostname():
                    self.log.append("advisory recommendation: PCGI_HOST '%s' doesn't match '%s'" % (hostname, socket.gethostname()))
            else:
                hostname = socket.gethostname()

        if port:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind((hostname, port))
            except socket.error:
                self.log.append("error creating/binding INET socket (%s, %s)" % (hostname, port))
                raise PcgiFileException
        else:
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            except socket.error:
                self.log.append("error creating UNIX socket")
                raise PcgiFileException

            socketFile = self.combined.get('PCGI_SOCKET_FILE')
            if os.path.exists(socketFile):
                self.log.append("advisory: socket %s in use, bind() not tested" % socketFile)
            else:
                try:
                    sock.bind(socketFile)
                    os.unlink(socketFile)
                except socket.error:
                    self.log.append("error binding UNIX socket (%s)" % socketFile)
                    raise PcgiFileException

    def checkWritePermissions(self):
        """
        Check write permissions for PCGI_SOCKET_FILE, PCGI_PID_FILE, and
        (if specified) PCGI_ERROR_LOG.
        """
        fn = {}
        if self.combined.has_key('PCGI_PID_FILE'):
            fn['PCGI_PID_FILE'] = self.combined['PCGI_PID_FILE']
        if self.combined.has_key('PCGI_SOCKET_FILE'):
            fn['PCGI_SOCKET_FILE'] = self.combined['PCGI_SOCKET_FILE']
        if self.combined.has_key('PCGI_ERROR_LOG'):
            fn['PCGI_ERROR_LOG'] = self.combined['PCGI_ERROR_LOG']
        for key, file in fn.items():
            if os.path.exists(file):
                try:
                    f = open(file,'a+')
                    f.close()
                except IOError:
                    self.log.append("%s write permission error: %s" % \
                                    (key, file))
                    raise PcgiFileException
            else:
                path = os.path.split(file)[0]
                import tempfile
                tempfile.tempdir = path
                tmpfile = tempfile.mktemp()
                try:
                    f = open(tmpfile,'w+')
                    f.close()
                    os.unlink(tmpfile)
                except IOError:
                    self.log.append("%s write permission error: %s" % \
                                    (key, file))
                    raise PcgiFileException

    def environList(self):
        """
        return a sorted list of how the environment would likely appear
        if run through the pcgi-wrapper.
        """
        e = []
        keys = self.combined.keys()
        keys.sort()
        for k in keys:
            e.append("%s\t%s" % (k, self.combined[k]))
        return e

    def getPcgiWrapperVersion(self):
        """
        Execute pcgi-wrapper with no arguments and grab the version id.
        """
        try:
            import tempfile
            tmpfile = tempfile.mktemp()
            os.system("%s > %s" % (self.pcgi_wrapper, tmpfile))
            f = open(tmpfile, 'r')
            r = f.readlines()
            f.close()
            os.unlink(tmpfile)
            for l in r:
                s = string.strip(l)
                if s[:21] == 'pcgi-wrapper-version ':
                    return string.split(s)[1]
        except ImportError:
            pass
        return None

    def isexecutable(self, path, real=None):
        if os.name == 'posix':
            return self.pathperm(path, real)[2]
        else:
            return 1

    def lookupPCGIPublisher(self):
        """
        The most efficient way for pcgi-wrapper to determine which
        pcgi_publisher to use is for the pcgi info file to specify
        it with the PCGI_PUBLISHER directive.  Using the PCGI_PUBLISHER
        is arguably the *best* method, as pcgi-wrapper will find it
        quicker than otherwise.  Still, in the interest of flexibility,
        pcgi-wrapper will attempt to locate pcgi_publisher using the
        following rules:

        1.  PCGI_PUBLISHER  (*best*)

        Rules 2-5, look in the paths below for files named: pcgi_publisher.py,
          pcgi_publisher.pyc, pcgi_publisher.pyo, pcgi_publisher.
        2.  PCGI_INSERT_PATH, if available
        3.  PYTHONPATH, if available
        4.  Look in the directory of PCGI_MODULE_PATH
        5.  Look in the directory of the pcgi info file
        """
        if self.combined.has_key('PCGI_PUBLISHER'):
            p = self.combined['PCGI_PUBLISHER']
            if os.path.isfile(p):
                self.resource.append("Publisher:\t%s" % p)
            else:
                self.log.append("publisher not found: %s" % p)
                raise PcgiFileException
            return
        self.log.append("advisory recommendation: specify PCGI_PUBLISHER")
        # search through combined PCGI_INSERT_PATH + PYTHONPATH directories
        searchPath = ""
        if self.combined.has_key('PCGI_INSERT_PATH'):
            searchPath = searchPath + self.combined['PCGI_INSERT_PATH']
        if self.combined.has_key('PYTHONPATH'):
            searchPath = searchPath + self.combined['PYTHONPATH']
        publisherName = ['pcgi_publisher.py','pcgi_publisher.pyc','pcgi_publisher.pyo','pcgi_publisher']
        for d in string.split(searchPath, ':'):
            for p in publisherName:
                pcgiPublisher = "%s%s%s" % (d, os.sep, p)
                if os.path.isfile(pcgiPublisher):
                    self.resource.append("Publisher:\t%s" % pcgiPublisher)
                    return
        # look in module directory
        if self.combined.has_key('PCGI_MODULE_PATH'):
            (d, x) = os.path.split(self.combined['PCGI_MODULE_PATH'])
            for p in publisherName:
                pcgiPublisher = "%s%s%s" % (d, os.sep, p)
                if os.path.isfile(pcgiPublisher):
                    self.resource.append("Publisher:\t%s" % pcgiPublisher)
                    return
        # look in pcgi info file directory
        (d, x) = os.path.split(self.pcgifile)
        for p in publisherName:
            pcgiPublisher = "%s%s%s" % (d, os.sep, p)
            if os.path.isfile(pcgiPublisher):
                self.resource.append("Publisher:\t%s" % pcgiPublisher)
                return
        self.log.append("Unable to locate the pcgi_publisher")
        raise PcgiFileException

    def pathperm(self, path, real=None):
        """
        Returns a 3-tuple of booleans indicating whether the process has
        (read, write, execute) permission.  A true value for the 'real'
        argument indicates the test should occur for the real id rather
        than the effective id.
        """
        stat = os.stat(path)
        if real is None:
            uid = os.geteuid()
            gid = os.getegid()
        else:
            uid = os.getuid()
            gid = os.getgid()

        if uid == stat[4]:
            return (00400 & stat[0], 00200 & stat[0], 00100 & stat[0])
        elif gid == stat[5]:
            return (00040 & stat[0], 00020 & stat[0], 00010 & stat[0])
        else:
            return (00004 & stat[0], 00002 & stat[0], 00001 & stat[0])

    def readInfoFile(self):
        max_directives = 12  # arbitrary number defined in pcgi.h
        if not os.path.isfile(self.pcgifile):
            self.log.append("unable to locate file: %s" % self.pcgifile)
            raise PcgiFileException
        elif not self.isexecutable(self.pcgifile):
            self.log.append("info file '%s' not executable" % self.pcgifile)
            raise PcgiFileException
        f = open(self.pcgifile, 'r')
        lc = 0
        for r in f.readlines():
            lc = lc + 1
            s = string.strip(r)
            self.file_contents.append(s)
            if lc == 1:
                if s[:2] != '#!':
                    self.log.append("first line missing header, e.g. #!/usr/local/bin/pcgi-wrapper")
                    raise PcgiFileException
                else:
                    self.pcgi_wrapper = string.strip(s[2:])
                    if not os.path.isfile(self.pcgi_wrapper):
                        self.log.append("unable to find wrapper: %s" % \
                                        self.pcgi_wrapper)
                        raise PcgiFileException
                    elif not self.isexecutable(self.pcgi_wrapper):
                        self.log.append("wrapper '%s' is not executable" % \
                                        self.pcgi_wrapper)
                        raise PcgiFileException

            if len(s) < 1 or s[0] == '#':
                continue
            pos = string.find(s, Delimiter)
            if pos < 0:
                self.log.append("missing '%s' delimiter at line %d: %s" % \
                                (Delimiter, lc, s))
            else:
                self.infodict[string.strip(s[0:pos])] = string.strip(s[pos+1:])
        f.close()
        if len(self.infodict.keys()) > max_directives:
            self.log.append("info fileexceeds maximum (%d) number of directives" % max_directives)
            raise PcgiFileException

class PcgiFileTest:
    """
    CGI sanity check of the pcgi info file.
    """
    def __init__(self):
        fs = cgi.FieldStorage()
        infofile = None
        if fs.has_key('infofile'):
            infofile = fs['infofile'].value
        elif fs.has_key('filename'):
            infofile = fs['filename'].value

        if infofile is None:
            print "Please specify the pcgi info file in the following manner:"
            print "<pre>"
            print "  http://.../cgi-bin/pcgifile.py?<STRONG>infofile=</STRONG><I>pcgifile</I>"
            print "</pre>"
            print "where <I>pcgifile</I> is the absolute path of the pcgi info file."
        else:
            print "<pre>"
            print "<strong>Python %s</strong>" % sys.version
            if os.environ.has_key('SERVER_SOFTWARE'):
                print "<strong>%s</strong>" % os.environ['SERVER_SOFTWARE']
                print
            print "PCGI info file:\t%s" % infofile
            pcgiFile = PcgiFile(infofile)
            print "PCGI wrapper:\t%s" % pcgiFile.pcgi_wrapper
            for m in pcgiFile.log:
                print m
            if not pcgiFile.continue_testing:
                print "status: FAILURE"
                print
                print "<STRONG>%s</STRONG>" % infofile
                for r in pcgiFile.file_contents:
                    print "  %s" % r
            else:
                print "looks OK"
                print
                print "<STRONG>%s</STRONG>" % infofile
                for r in pcgiFile.file_contents:
                    print "  %s" % r
                print
                print "<STRONG>Likely publisher resource values:</STRONG>"
                for r in pcgiFile.resource:
                    print "  %s" % r
                print
                print "<STRONG>Versions of modules used:</STRONG>"
                for r in pcgiFile.module_version:
                    print "  %s" % r
                print
                print "<STRONG>Resulting environment will probably appear to the publisher as:</STRONG>"
                for e in pcgiFile.environList():
                    print "  %s" % e

def test():
    usage = 'usage: pcgifile pcgi_info_file'
    if len(sys.argv) < 2:
        print usage
        sys.exit(1)
    infoFile = sys.argv[1]
    pcgiFile = PcgiFile(infoFile)
    for m in pcgiFile.log:
        print m
    if pcgiFile.continue_testing:
        print "%s looks OK" % infoFile

if __name__ == '__main__':
    try:
        import cgi, os, sys, string, traceback
        if os.environ.has_key('SERVER_PROTOCOL'):
            print "Content-type: text/html"
            print "Expires: Monday, 1-Jan-96 00:00:00 GMT"
            print "Pragma: no-cache"
            print
            sys.stderr = sys.stdout
            try:
                pcgiFileTest = PcgiFileTest()
            except:
                print "<pre>"
                traceback.print_exc()
        else:
            test()
    except ImportError:
        print "Content-type: text/html"
        print
        print "error during python imports; to fix try adding to pcgifile.py: <br><pre>"
        print "    sys.path[0:0] = [path1, path2, ...]"
