import os

from misc.factory import Factory

# generic datatypes

def security_policy_implementation(value):
    value = value.upper()
    ok = ('PYTHON', 'C')
    if value not in ok:
        raise ValueError, (
            "security_policy_implementation must be one of %s" % ok
            )
    return value

def use_daemon_process(value):
    from ZConfig.datatypes import asBoolean
    daemonize = asBoolean(value)
    # cannot use daemon process on non-POSIX platforms
    if os.name != 'posix':
        return False
    return daemonize

# log-related datatypes
# (the loghandler datatypes come from the zLOG package)

def logger(section):
    return LoggerWrapper(section.getSectionName(),
                         section.level,
                         section.handlers)

# database-related datatypes

def mount_point(value):
    if value.startswith('/'):
        return value
    raise ValueError, (
        'Invalid mount_point "%s" (must start with a slash)' % value
        )

def database(section):
    if len(section.storages) > 1:
        raise ValueError, ('Current database support limits database '
                           'instances to a single storage')
    if len(section.storages) < 1:
        raise ValueError, 'Must name one storage in a database section'
    klass = section.db_class
    mounts = section.mount_points
    dbfactory = Factory(
        klass, None,
        pool_size=section.pool_size,
        cache_size=section.cache_size,
        cache_deactivate_after=section.cache_deactivate_after,
        version_pool_size=section.version_pool_size,
        version_cache_size=section.version_cache_size,
        version_cache_deactivate_after=section.version_cache_deactivate_after)
    storagefactory = section.storages[0]
    return mounts, DBWrapper(dbfactory, storagefactory)

def filestorage(section):
    return Factory('ZODB.FileStorage.FileStorage', None, section.path,
                   create=section.create,
                   read_only=section.read_only,
                   stop=section.stop,
                   quota=section.quota)

def mappingstorage(section):
    name = section.name
    return Factory('ZODB.MappingStorage.MappingStorage', None, name)

def clientstorage(section):
    return Factory('ZEO.ClientStorage.ClientStorage', None, section.addr,
                   storage=section.storage,
                   cache_size=section.cache_size,
                   name=section.name,
                   client=section.client,
                   debug=section.debug,
                   var=section.var,
                   min_disconnect_poll=section.min_disconnect_poll,
                   max_disconnect_poll=section.max_disconnect_poll,
                   wait=section.wait,
                   read_only=section.read_only,
                   read_only_fallback=section.read_only_fallback)

_marker = object()

class LoggerWrapper:
    """
    A wrapper used to create loggers while delaying actual logger
    instance construction.  We need to do this because we may
    want to reference a logger before actually instantiating it (for example,
    to allow the app time to set an effective user).
    An instance of this wrapper is a callable which, when called, returns a
    logger object.
    """
    def __init__(self, name, level, handler_factories):
        self.name = name
        self.level = level
        self.handler_factories = handler_factories
        self.resolved = _marker

    def __call__(self):
        if self.resolved is _marker:
            # set the logger up
            import logging
            logger = logging.getLogger(self.name)
            logger.handlers = []
            logger.propagate = 0
            logger.setLevel(self.level)
            for handler_factory in self.handler_factories:
                handler = handler_factory()
                logger.addHandler(handler)
            self.resolved = logger
        return self.resolved

class DBWrapper:
    """
    A wrapper used to create ZODB databases while delaying the underlying
    storage instance construction.  We need to do this because we may
    want to reference a database before actually instantiating it (for
    example, in order to delay database construction until after an
    effective user is set or until all configuration parsing is done).
    An instance of this wrapper is a callable which, when called, returns a
    database object.
    """
    def __init__(self, dbfactory, storagefactory):
        self.dbfactory = dbfactory
        self.storagefactory = storagefactory
        self.resolved = _marker

    def __call__(self):
        if self.resolved is _marker:
            args, kw = self.dbfactory.getArgs()
            args = [self.storagefactory()] + list(args)
            self.dbfactory.setArgs(args, kw)
            self.resolved = self.dbfactory()
        return self.resolved
