from ConfigParser import ConfigParser
CP = ConfigParser()
CP.read(('versions-zope3.cfg', 'versions-zope2.cfg'))

def getVersionForPackage(package):
    """ Return the version for a package (used in setup.py) """
    return CP.get('versions', package)

if __name__ == '__main__':
    for package in ('ZODB3', 'pytz', 'does.not.exisit'):
        print package, getVersionForPackage(package)

