import os
import re
import sys
from socket import gethostbyaddr

from Zope2.Startup import config


def _setenv(name, value):
    if isinstance(value, str):
        os.environ[name] = value
    else:
        os.environ[name] = repr(value)


def debug_mode(value):
    value and _setenv('Z_DEBUG_MODE', '1')
    return value


def locale(value):
    import locale
    locale.setlocale(locale.LC_ALL, value)
    return value


def datetime_format(value):
    value and _setenv('DATETIME_FORMAT', value)
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


def large_file_threshold(value):
    config.ZSERVER_LARGE_FILE_THRESHOLD = value


def http_realm(value):
    value is not None and _setenv('Z_REALM', value)
    return value


def max_listen_sockets(value):
    config.ZSERVER_CONNECTION_LIMIT = value


def cgi_maxlen(value):
    import cgi
    cgi.maxlen = value


def http_header_max_length(value):
    return value


def enable_ms_public_header(value):
    config.ZSERVER_ENABLE_MS_PUBLIC_HEADER = value


def root_handler(cfg):
    """ Mutate the configuration with defaults and perform
    fixups of values that require knowledge about configuration
    values outside of their context.
    """

    # Set environment variables
    for k, v in cfg.environment.items():
        os.environ[k] = v

    # Add directories to the pythonpath
    instancelib = os.path.join(cfg.instancehome, 'lib', 'python')
    if instancelib not in cfg.path:
        if os.path.isdir(instancelib):
            cfg.path.append(instancelib)
    path = cfg.path[:]
    path.reverse()
    for dir in path:
        sys.path.insert(0, dir)

    # Add any product directories not already in Products.__path__.
    # Directories are added in the order they are mentioned

    instanceprod = os.path.join(cfg.instancehome, 'Products')
    if instanceprod not in cfg.products:
        if os.path.isdir(instanceprod):
            cfg.products.append(instanceprod)

    import Products
    L = []
    for d in cfg.products + Products.__path__:
        if d not in L:
            L.append(d)
    Products.__path__[:] = L

    # if no servers are defined, create default http server and ftp server
    if not cfg.servers:
        cfg.servers = []

    # prepare servers:
    for factory in cfg.servers:
        factory.prepare(cfg.ip_address or '',
                        cfg.dns_resolver,
                        "Zope2",
                        cfg.cgi_environment,
                        cfg.port_base)

    # set up trusted proxies
    if cfg.trusted_proxies:
        mapped = []
        for name in cfg.trusted_proxies:
            mapped.extend(_name2Ips(name))
        config.TRUSTED_PROXIES = tuple(mapped)

        from ZPublisher import HTTPRequest
        HTTPRequest.trusted_proxies = tuple(mapped)

    # set the maximum number of ConflictError retries
    if cfg.max_conflict_retries:
        from ZPublisher import HTTPRequest
        HTTPRequest.retry_max_count = cfg.max_conflict_retries


def handleConfig(cfg, multihandler):
    handlers = {}
    for name, value in globals().items():
        if not name.startswith('_'):
            handlers[name] = value
    return multihandler(handlers)


def _name2Ips(host, isIp_=re.compile(r'(\d+\.){3}').match):
    """Map a name *host* to the sequence of its ip addresses.

    use *host* itself (as sequence) if it already is an ip address.
    Thus, if only a specific interface on a host is trusted,
    identify it by its ip (and not the host name).
    """
    if isIp_(host):
        return [host]
    return gethostbyaddr(host)[2]
