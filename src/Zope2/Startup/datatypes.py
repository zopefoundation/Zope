##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""Datatypes for the Zope schema for use with ZConfig."""

import os
from UserDict import UserDict

from ZConfig.components.logger import logger
from ZODB.config import ZODBDatabase

# generic datatypes

def security_policy_implementation(value):
    value = value.upper()
    ok = ('PYTHON', 'C')
    if value not in ok:
        raise ValueError, (
            "security-policy-implementation must be one of %s" % repr(ok)
            )
    return value

def datetime_format(value):
    value = value.lower()
    ok = ('us', 'international')
    if value not in ok:
        raise ValueError, (
            "datetime-format must be one of %r" % repr(ok)
            )
    return value

def cgi_environment(section):
    return section.environ

# Datatype for the access and trace logs
# (the loghandler datatypes come from the zLOG package)

class LoggerFactory(logger.LoggerFactory):
    """
    A factory used to create loggers while delaying actual logger
    instance construction.  We need to do this because we may want to
    reference a logger before actually instantiating it (for example,
    to allow the app time to set an effective user).  An instance of
    this wrapper is a callable which, when called, returns a logger
    object.
    """
    def __init__(self, section):
        section.name = section.getSectionName()
        section.propagate = False
        logger.LoggerFactory.__init__(self, section)

# DNS resolver

def dns_resolver(hostname):
    from ZServer.medusa import resolver
    return resolver.caching_resolver(hostname)

# mount-point definition

def mount_point(value):
    if not value:
        raise ValueError, 'mount-point must not be empty'
    if not value.startswith('/'):
        raise ValueError, ("mount-point '%s' is invalid: mount points must "
                           "begin with a slash" % value)
    return value

# A datatype that converts a Python dotted-path-name to an object

def importable_name(name):
    try:
        components = name.split('.')
        start = components[0]
        g = globals()
        package = __import__(start, g, g)
        modulenames = [start]
        for component in components[1:]:
            modulenames.append(component)
            try:
                package = getattr(package, component)
            except AttributeError:
                n = '.'.join(modulenames)
                package = __import__(n, g, g, component)
        return package
    except ImportError:

        import traceback, cStringIO
        IO = cStringIO.StringIO()
        traceback.print_exc(file=IO)
        raise ValueError(
            'The object named by "%s" could not be imported\n%s' %  (name, IO.getvalue()))

# A datatype that ensures that a dotted path name can be resolved but
# returns the name instead of the object

def python_dotted_path(name):
    ob = importable_name(name) # will fail in course
    return name


class zdaemonEnvironDict(UserDict):
    # zdaemon 2 expects to use a 'mapping' attribute of the environ object.
    @property
    def mapping(self):
        return self.data

# Datatype for the root configuration object
# (adds the softwarehome and zopehome fields; default values for some
#  computed paths, configures the dbtab)

def root_config(section):
    from ZConfig import ConfigurationError
    from ZConfig.matcher import SectionValue
    here = os.path.dirname(os.path.abspath(__file__))
    swhome = os.path.dirname(os.path.dirname(here))
    section.softwarehome = swhome
    section.zopehome = os.path.dirname(os.path.dirname(swhome))
    if section.environment is None:
        section.environment = zdaemonEnvironDict()
    if section.cgi_environment is None:
        section.cgi_environment = zdaemonEnvironDict()
    if section.clienthome is None:
        section.clienthome = os.path.join(section.instancehome, "var")
    # set up defaults for pid_filename and lock_filename if they're
    # not in the config
    if section.pid_filename is None:
        section.pid_filename = os.path.join(section.clienthome, 'Z2.pid')
    if section.lock_filename is None:
        section.lock_filename = os.path.join(section.clienthome, 'Z2.lock')

    if not section.databases:
        section.databases = []

    mount_factories = {} # { name -> factory}
    mount_points = {} # { virtual path -> name }
    dup_err = ('Invalid configuration: ZODB databases named "%s" and "%s" are '
               'both configured to use the same mount point, named "%s"')

    for database in section.databases:
        points = database.getVirtualMountPaths()
        name = database.config.getSectionName()
        mount_factories[name] = database
        for point in points:
            if mount_points.has_key(point):
                raise ConfigurationError(dup_err % (mount_points[point],
                                                    name, point))
            mount_points[point] = name
    section.dbtab = DBTab(mount_factories, mount_points)
    pconfigs = {}
    for pconfig in section.product_config:
        section_name = pconfig.getSectionName()
        if isinstance(pconfig, SectionValue):
            section_type = pconfig.getSectionType()
            if section_type == 'product-config':
                pconfigs[section_name] = pconfig.mapping
            else:
                pconfigs[section_name] = pconfig
        else:
            pconfigs[section_name] = pconfig

    section.product_config = pconfigs

    return section

class ZopeDatabase(ZODBDatabase):
    """ A ZODB database datatype that can handle an extended set of
    attributes for use by DBTab """

    def createDB(self, database_name, databases):
        self.config.database_name = database_name
        return ZODBDatabase.open(self, databases)

    def open(self, database_name, databases):
        DB = self.createDB(database_name, databases)
        if self.config.connection_class:
            # set the connection class
            DB.klass = self.config.connection_class
        if self.config.class_factory is not None:
            DB.classFactory = self.config.class_factory
        from ZODB.ActivityMonitor import ActivityMonitor
        DB.setActivityMonitor(ActivityMonitor())
        return DB

    def getName(self):
        return self.name

    def computeMountPaths(self):
        mps = []
        for part in self.config.mount_points:
            real_root = None
            if ':' in part:
                # 'virtual_path:real_path'
                virtual_path, real_path = part.split(':', 1)
                if real_path.startswith('~'):
                    # Use a special root.
                    # 'virtual_path:~real_root/real_path'
                    real_root, real_path = real_path[1:].split('/', 1)
            else:
                # Virtual path is the same as the real path.
                virtual_path = real_path = part
            mps.append((virtual_path, real_root, real_path))
        return mps

    def getVirtualMountPaths(self):
        return [item[0] for item in self.computeMountPaths()]

    def getMountParams(self, mount_path):
        """Returns (real_root, real_path, container_class) for a virtual
        mount path.
        """
        for (virtual_path, real_root, real_path) in self.computeMountPaths():
            if virtual_path == mount_path:
                container_class = self.config.container_class
                if not container_class and virtual_path != '/':
                    # default to OFS.Folder.Folder for nonroot mounts
                    # if one isn't specified in the config
                    container_class = 'OFS.Folder.Folder'
                return (real_root, real_path, container_class)
        raise LookupError('Nothing known about mount path %s' % mount_path)
    
def default_zpublisher_encoding(value):
    # This is a bit clunky but necessary :-(
    # These modules are imported during the configuration process
    # so a module-level call to getConfiguration in any of them
    # results in getting config data structure without the necessary
    # value in it.
    from ZPublisher import Converters, HTTPRequest, HTTPResponse
    Converters.default_encoding = value
    HTTPRequest.default_encoding = value
    HTTPResponse.default_encoding = value

class DBTab:
    """A Zope database configuration, similar in purpose to /etc/fstab.
    """

    def __init__(self, db_factories, mount_paths):
        self.db_factories = db_factories  # { name -> DatabaseFactory }
        self.mount_paths = mount_paths    # { virtual path -> name }
        self.databases = {}               # { name -> DB instance }

    def listMountPaths(self):
        """Returns a sequence of (virtual_mount_path, database_name).
        """
        return self.mount_paths.items()


    def listDatabaseNames(self):
        """Returns a sequence of names.
        """
        return self.db_factories.keys()


    def hasDatabase(self, name):
        """Returns true if name is the name of a configured database."""
        return self.db_factories.has_key(name)


    def _mountPathError(self, mount_path):
        from ZConfig import ConfigurationError
        if mount_path == '/':
            raise ConfigurationError(
                "No root database configured")
        else:
            raise ConfigurationError(
                "No database configured for mount point at %s"
                % mount_path)

    def getDatabase(self, mount_path=None, name=None, is_root=0):
        """Returns an opened database.  Requires either mount_path or name.
        """
        if name is None:
            name = self.getName(mount_path)
        db = self.databases.get(name, None)
        if db is None:
            factory = self.getDatabaseFactory(name=name)
            db = factory.open(name, self.databases)
        return db

    def getDatabaseFactory(self, mount_path=None, name=None):
        if name is None:
            name = self.getName(mount_path)
        if not self.db_factories.has_key(name):
            raise KeyError('%s is not a configured database' % repr(name))
        return self.db_factories[name]

    def getName(self, mount_path):
        name = self.mount_paths.get(mount_path)
        if name is None:
            self._mountPathError(mount_path)
        return name

# class factories (potentially) used by the class-factory parameter in
# zopeschema.xml

def minimalClassFactory(jar, module, name,
                        _silly=('__doc__',), _globals={},
                        ):
    """Minimal class factory.

    If any class is not found, this class factory will propagate
    the exception to the application, unlike the other class factories.
    """
    m = __import__(module, _globals, _globals, _silly)
    return getattr(m, name)

def simpleClassFactory(jar, module, name,
                       _silly=('__doc__',), _globals={},
                       ):
    """Class factory.
    """
    import OFS.Uninstalled
    try:
        m = __import__(module, _globals, _globals, _silly)
        return getattr(m, name)
    except:
        return OFS.Uninstalled.Broken(jar, None, (module, name))
