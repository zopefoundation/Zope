"""Server Zope from a basic Python web server
"""

import ZopeHTTPServer, os

ZopeHTTPServer.main(os.path.join(os.getcwd(),'lib','python','Main.py'))
                    
