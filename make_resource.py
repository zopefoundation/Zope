"""Build a PCGI resource file.

You must be in the directory containing this script.
"""
print
print '-'*78

from do import *

python=sys.executable
name=os.environ.get('ZNAME','Zope')
print 'Writing the pcgi resource file (ie cgi script), %s.cgi' % name
cwd=os.environ.get('ZDIR',os.getcwd())

open('%s.cgi' % name,'w').write('''#!%(cwd)s/pcgi/pcgi-wrapper
PCGI_NAME=Main
PCGI_MODULE_PATH=%(cwd)s/lib/python/Main.py
PCGI_PUBLISHER=%(cwd)s/pcgi/pcgi_publisher.py
PCGI_EXE=%(python)s
PCGI_SOCKET_FILE=%(cwd)s/var/pcgi.soc
PCGI_PID_FILE=%(cwd)s/var/pcgi.pid
PCGI_ERROR_LOG=%(cwd)s/var/pcgi.log
PCGI_DISPLAY_ERRORS=1
BOBO_REALM=%(name)s
BOBO_DEBUG_MODE=1
INSTANCE_HOME=%(cwd)s
''' % vars())

do('chmod 755 %s.cgi' % name)
