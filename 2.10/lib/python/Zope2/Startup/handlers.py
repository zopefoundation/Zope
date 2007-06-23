import os
import sys
import time
import logging
from re import compile
from socket import gethostbyaddr

try:
    import twisted.internet
    from twisted.application.service import MultiService
    import zope.app.appsetup.interfaces
    import zope.app.twisted.main

    import twisted.web2.wsgi
    import twisted.web2.server
    import twisted.web2.log
    
    try:
        from twisted.web2.http import HTTPFactory
    except ImportError:
        from twisted.web2.channel.http import HTTPFactory
    
    from zope.component import provideUtility
    from zope.app.twisted.server import ServerType, SSLServerType
    from zope.app.twisted.interfaces import IServerType
    from ZPublisher.WSGIPublisher import publish_module
    
    _use_twisted = True
except ImportError:
    _use_twisted = False

# top-level key handlers


# XXX  I suspect there are still problems here.  In most cases, if the
# value is not set from the config file, or if the value is the
# default, the corresponding envvar is not unset, which is needed to
# ensure that the environment variables and the configuration values
# reflect a coherant configuration.

def _setenv(name, value):
    if isinstance(value, str):
        os.environ[name] = value
    else:
        os.environ[name] = `value`

def debug_mode(value):
    value and _setenv('Z_DEBUG_MODE', '1')
    import Globals
    Globals.DevelopmentMode = not not value
    return value

def locale(value):
    import locale
    locale.setlocale(locale.LC_ALL, value)
    return value

def datetime_format(value):
    value and _setenv('DATETIME_FORMAT', value)
    return value

def zserver_read_only_mode(value):
    value and _setenv('ZOPE_READ_ONLY', '1')
    return value

def automatically_quote_dtml_request_data(value):
    not value and _setenv('ZOPE_DTML_REQUEST_AUTOQUOTE', '0')
    return value

def maximum_number_of_session_objects(value):
    default = 1000
    value not in (None, default) and _setenv('ZSESSION_OBJECT_LIMIT', value)
    return value

def session_add_notify_script_path(value):
    value is not None and _setenv('ZSESSION_ADD_NOTIFY', value)
    return value

def session_delete_notify_script_path(value):
    value is not None and _setenv('ZSESSION_DEL_NOTIFY', value)
    return value

def session_timeout_minutes(value):
    default = 20
    value not in (None, default) and _setenv('ZSESSION_TIMEOUT_MINS', value)
    return value

def suppress_all_access_rules(value):
    value and _setenv('SUPPRESS_ACCESSRULE', value)
    return value

def suppress_all_site_roots(value):
    value and _setenv('SUPPRESS_SITEROOT', value)
    return value

def database_quota_size(value):
    value and _setenv('ZOPE_DATABASE_QUOTA', value)
    return value

def read_only_database(value):
    value and _setenv('ZOPE_READ_ONLY', '1')
    return value

def zeo_client_name(value):
    value and _setenv('ZEO_CLIENT', value)
    return value

def structured_text_header_level(value):
    value is not None and _setenv('STX_DEFAULT_LEVEL', value)
    return value

def rest_input_encoding(value):
    value and _setenv('REST_INPUT_ENCODING' , value)
    return value

def rest_output_encoding(value):
    value and _setenv('REST_OUTPUT_ENCODING' , value)
    return value

def rest_header_level(value):
    value and _setenv('REST_DEFAULT_LEVEL' , value)
    return value

def rest_language_code(value):
    value and _setenv('REST_LANGUAGE_CODE' , value)
    return value

def large_file_threshold(value):
    import ZServer
    ZServer.LARGE_FILE_THRESHOLD = value

def publisher_profile_file(value):
    value is not None and _setenv('PROFILE_PUBLISHER', value)
    from ZPublisher.Publish import install_profiling
    install_profiling(value)
    return value

def http_realm(value):
    value is not None and _setenv('Z_REALM', value)
    return value

def max_listen_sockets(value):
    import ZServer
    ZServer.CONNECTION_LIMIT = value

def cgi_maxlen(value):
    import cgi
    cgi.maxlen = value

def http_header_max_length(value):
    return value

def catalog_getObject_raises(value):

    if value is not None:

        import warnings
        warnings.warn(
        "'catalog-getObject-raises' option will be removed in Zope 2.10:\n",
        DeprecationWarning)

        from Products.ZCatalog import CatalogBrains
        CatalogBrains.GETOBJECT_RAISES = bool(value)

    return value

# server handlers

def root_handler(config):
    """ Mutate the configuration with defaults and perform
    fixups of values that require knowledge about configuration
    values outside of their context.
    """

    # Set environment variables
    for k,v in config.environment.items():
        os.environ[k] = v

    # Add directories to the pythonpath; always insert instancehome/lib/python
    instancelib = os.path.join(config.instancehome, 'lib', 'python')
    if instancelib not in config.path:
        config.path.append(instancelib)
    path = config.path[:]
    path.reverse()
    for dir in path:
        sys.path.insert(0, dir)

    # Add any product directories not already in Products.__path__.
    # Directories are added in the order they are mentioned
    # Always insert instancehome.Products

    instanceprod = os.path.join(config.instancehome, 'Products')
    if instanceprod not in config.products:
        config.products.append(instanceprod)

    import Products
    L = []
    for d in config.products + Products.__path__:
        if d not in L:
            L.append(d)
    Products.__path__[:] = L

    # Augment the set of MIME types:
    if config.mime_types:
        from zope.contenttype import add_files
        add_files(config.mime_types)

    # if no servers are defined, create default http server and ftp server
    if not config.servers:
        config.servers = []

    # prepare servers:
    for factory in config.servers:
        factory.prepare(config.ip_address or '',
                        config.dns_resolver,
                        "Zope2",
                        config.cgi_environment,
                        config.port_base)

    if not config.twisted_servers:
        config.twisted_servers = []
    else:
        # Set number of threads (reuse zserver_threads variable)
        twisted.internet.reactor.suggestThreadPoolSize(config.zserver_threads)

        # Create a root service
        rootService = MultiService()

        for server in config.twisted_servers:
            service = server.create(None)
            service.setServiceParent(rootService)

        rootService.startService()
        twisted.internet.reactor.addSystemEventTrigger(
            'before', 'shutdown', rootService.stopService)

    # set up trusted proxies
    if config.trusted_proxies:
        import ZPublisher.HTTPRequest
        # DM 2004-11-24: added host name mapping (such that examples in
        # conf file really have a chance to work
        mapped = []
        for name in config.trusted_proxies: mapped.extend(_name2Ips(name))
        ZPublisher.HTTPRequest.trusted_proxies = tuple(mapped)


def handleConfig(config, multihandler):
    handlers = {}
    for name, value in globals().items():
        if not name.startswith('_'):
            handlers[name] = value
    return multihandler(handlers)

# DM 2004-11-24: added
def _name2Ips(host, isIp_=compile(r'(\d+\.){3}').match):
    '''map a name *host* to the sequence of its ip addresses;
    use *host* itself (as sequence) if it already is an ip address.
    Thus, if only a specific interface on a host is trusted,
    identify it by its ip (and not the host name).
    '''
    if isIp_(host): return [host]
    return gethostbyaddr(host)[2]


# Twisted support:

def createHTTPFactory(ignored):
    resource = twisted.web2.wsgi.WSGIResource(publish_module)
    resource = twisted.web2.log.LogWrapperResource(resource)

    return HTTPFactory(twisted.web2.server.Site(resource))

if _use_twisted:
    http = ServerType(createHTTPFactory, 8080)
    provideUtility(http, IServerType, 'Zope2-HTTP')
