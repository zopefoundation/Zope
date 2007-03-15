##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ztc_common.py

This file must be called from framework.py like so

  execfile(os.path.join(os.path.dirname(Testing.__file__),
           'ZopeTestCase', 'ztc_common.py'))

$Id$
"""

# Overwrites the default framework() method to expose the
# TestRunner parameters
#
def framework(stream=sys.stderr, descriptions=1, verbosity=1):
    if __name__ != '__main__':
        return

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        sys.exit(globals()[arg]() and 1 or 0)

    result = TestRunner(stream, descriptions, verbosity).run(test_suite())
    sys.exit(len(result.errors) + len(result.failures))


# Configures the Zope environment
#
class Configurator:

    def __init__(self):
        '''Sets up the configurator.'''
        self.cwd = self.realpath(os.getcwd())
        self.software_home = self.realpath(os.environ.get('SOFTWARE_HOME', ''))
        self.instance_home = self.realpath(globals()['__INSTANCE_HOME'])
        self.zeo_instance_home = self.realpath(os.environ.get('ZEO_INSTANCE_HOME', ''))
        self.zope_config = self.realpath(os.environ.get('ZOPE_CONFIG', ''))

    def run(self):
        '''Runs the configurator.'''
        if self.zope_config:    
            # Don't configure anything if people use the ZOPE_CONFIG patch
            return
        if self.zeo_instance_home:
            self.setup_zeo_instance_home()
        else:
            if self.instance_home:
                self.setup_instance_home()
            else:
                self.detect_and_setup_instance_home()
            self.setup_custom_zodb()
    
    def setup_zeo_instance_home(self):
        '''If ZEO_INSTANCE_HOME has been given, assume a ZEO setup and use the
           instance's custom_zodb.py to connect to a running ZEO server.'''
        if os.path.isdir(os.path.join(self.zeo_instance_home, 'Products')):
            if os.path.exists(os.path.join(self.zeo_instance_home, 'custom_zodb.py')):
                self.add_instance(self.zeo_instance_home)
                if self.getconfig('testinghome'):
                    self.setconfig(testinghome=self.zeo_instance_home)
                    self.setconfig(instancehome=self.zeo_instance_home)
                else:
                    os.environ['INSTANCE_HOME'] = INSTANCE_HOME = self.zeo_instance_home
                    self.setconfig(instancehome=self.zeo_instance_home)
            else:
                print 'Unable to locate custom_zodb.py in %s.' % self.zeo_instance_home
                sys.exit(1)
        else:
            print 'Unable to locate Products directory in %s.' % self.zeo_instance_home
            sys.exit(1)

    def setup_instance_home(self):
        '''If INSTANCE_HOME has been given, add the instance's Products
           and lib/python directories to the appropriate paths.'''
        if os.path.isdir(os.path.join(self.instance_home, 'Products')):
            self.add_instance(self.instance_home)
            if self.getconfig('testinghome'):
                self.setconfig(instancehome=self.instance_home)
        else:
            print 'Unable to locate Products directory in %s.' % self.instance_home
            sys.exit(1)

    def detect_and_setup_instance_home(self):
        '''If INSTANCE_HOME has not been given, try to detect whether we run
           in an instance home installation by walking up from cwd until we
           find a 'Products' dir.'''
        if not self.cwd.startswith(self.software_home):
            p = d = self.cwd
            while d:
                if os.path.isdir(os.path.join(p, 'Products')):
                    self.add_instance(p)
                    if self.getconfig('testinghome'):
                        self.setconfig(instancehome=p)
                    break
                p, d = os.path.split(p)
            else:
                print 'Unable to locate Products directory.',
                print 'You might need to set INSTANCE_HOME.'
                sys.exit(1)

    def setup_custom_zodb(self):
        '''If there is a custom_zodb.py file in the tests dir, use it.
           Note that the instance has already been set at this point
           so redirecting INSTANCE_HOME should be safe.'''
        if os.path.exists(os.path.join(self.cwd, 'custom_zodb.py')):
            if self.getconfig('testinghome'):
                self.setconfig(testinghome=self.cwd)
            else:
                os.environ['INSTANCE_HOME'] = INSTANCE_HOME = self.cwd
                self.setconfig(instancehome=self.cwd)

    def add_instance(self, p):
        '''Adds an INSTANCE_HOME directory to Products.__path__ and sys.path.'''
        import Products
        products = os.path.join(p, 'Products')
        if os.path.isdir(products) and products not in Products.__path__:
            Products.__path__.insert(0, products)
        libpython = os.path.join(p, 'lib', 'python')
        if os.path.isdir(libpython) and libpython not in sys.path:
            sys.path.insert(0, libpython)

    def getconfig(self, key):
        '''Reads a value from Zope configuration.'''
        try:
            import App.config
        except ImportError:
            pass
        else:
            config = App.config.getConfiguration()
            return getattr(config, key, None)

    def setconfig(self, **kw):
        '''Updates Zope configuration'''
        try:
            import App.config
        except ImportError:
            pass
        else:
            config = App.config.getConfiguration()
            for key, value in kw.items():
                setattr(config, key, value)
            App.config.setConfiguration(config)

    def realpath(self, path):
        try:
            from os.path import realpath
        except ImportError:
            try:
                from App.Common import realpath
            except ImportError:
                realpath = os.path.abspath
        if not path:
            return path
        return realpath(path)


if __name__ == '__main__':
    Configurator().run()
    del Configurator

