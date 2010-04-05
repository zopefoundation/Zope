"""
Generate an index file based on the version.cfg file of Zope 2
in order to provide a version specific index page generated to be used
in combination with easy_install -i <some_url>
"""

import os
import sys
import urlparse
from xmlrpclib import Server
from ConfigParser import RawConfigParser as ConfigParser

class CasePreservingConfigParser(ConfigParser):

    def optionxform(self, option):
        return option  # don't flatten case!

def write_index(package, version):
    print >>sys.stderr, 'Package %s==%s' % (package, version)
    dest_dir = os.path.join(dirname, package)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    index_html = os.path.join(dest_dir, 'index.html')

    fp = file(index_html, 'w')
    print >>fp, '<html><body>'
    lst = server.package_urls(package, version)
    if lst:
        # package hosted on PyPI
        for d in lst:
            link = '<a href="%s">%s</a>' % (d['url'], d['filename'])
            print >>fp, link
            print >>fp, '<br/>'
    else:
        # for externally hosted packages we need to rely on the 
        # download_url metadata
        rel_data = server.release_data(package, version)
        download_url = rel_data['download_url']
        filename = os.path.basename(urlparse.urlparse(download_url)[2])
        link = '<a href="%s">%s</a>' % (download_url, filename)
        print >>fp, link

    print >>fp, '</body></html>'
    fp.close()

CP = CasePreservingConfigParser()
CP.read(['versions.cfg'])

server = Server('http://pypi.python.org/pypi')
links = list()
dirname = sys.argv[1]

write_index('Zope2', '2.12.3')

for package in CP.options('versions'):

    version = CP.get('versions', package)
    write_index(package, version)
