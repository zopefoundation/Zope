"""
Generate an index file based on the version.cfg file of Zope 2
in order to provide a version specific index page generated to be used
in combination with easy_install -i <some_url>/index.html
"""

import sys
from xmlrpclib import Server
from ConfigParser import ConfigParser

CP = ConfigParser()
CP.read(['versions.cfg'])

server = Server('http://pypi.python.org/pypi')
links = list()

for package in CP.options('versions'):
    version = CP.get('versions', package)
    print >>sys.stderr, 'Package %s==%s' % (package, version)
    for d in server.package_urls(package, version):
        links.append('<a href="%s">%s</a>' % (d['url'], d['filename']))

fp = file('index.html', 'w')
print >>fp, '<html><body>'
for link in links:
    print >>fp, link
    print >>fp, '<br/>'
print >>fp, '</body></html>'

fp.close()
