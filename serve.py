"""Server Zope from a basic Python web server
"""

import ZopeHTTPServer, os, sys

args=sys.argv[1:]+[os.path.join(os.getcwd(),'lib','python','Main.py')]

ZopeHTTPServer.main(args)
                    
