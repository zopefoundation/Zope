import os
import sys

import Zope2
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.users import system as user
from Testing.makerequest import makerequest
from Zope2.Startup.run import make_wsgi_app
from zope.globalrequest import setRequest


def runscript(zopeconf, script_name, *extra_args):
    make_wsgi_app({}, zopeconf)
    app = Zope2.app()
    app = makerequest(app)
    app.REQUEST['PARENTS'] = [app]
    setRequest(app.REQUEST)
    newSecurityManager(None, user)
    scriptglobals = {'__name__': '__main__', 'app': app}
    with open(script_name) as script:
        scriptcode = script.read()
    exec(compile(scriptcode, script_name, 'exec'), scriptglobals)


def debug(zopeconf):
    make_wsgi_app({}, zopeconf)
    print('Starting debugger (the name "app" is bound to the top-level '
          'Zope object)')
    return Zope2.app()


def debug_console(zopeconf):
    cmd = f'{sys.executable} -i -c "import sys; sys.path={sys.path}; from Zope2.utilities.zconsole import debug; app = debug(\\\"{zopeconf}\\\")"'  # noqa: E501
    os.system(cmd)


def main(args=sys.argv):
    import argparse
    parser = argparse.ArgumentParser(description='Zope console')
    parser.add_argument(
        'mode',
        choices=['run', 'debug'],
        help='mode of operation, run: run script; debug: interactive console')  # noqa: E501
    parser.add_argument('zopeconf', help='path to zope.conf')
    parser.add_argument('scriptargs', nargs=argparse.REMAINDER)
    namespace, unused = parser.parse_known_args(args[1:])
    if namespace.mode == 'debug':
        debug_console(namespace.zopeconf)
    elif namespace.mode == 'run':
        runscript(namespace.zopeconf, *namespace.scriptargs)


if __name__ == '__main__':
    main()
