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

import os
import re
from socket import gethostbyaddr

from zope.deferredimport import deprecated

# BBB Zope 5.0
_prefix = 'ZServer.Zope2.Startup.handlers:'
deprecated(
    'Please import from ZServer.Zope2.Startup.handlers.',
    handleConfig=_prefix + 'handleConfig',
    root_handler=_prefix + 'root_handler',
    maximum_number_of_session_objects=(
        _prefix + 'maximum_number_of_session_objects'),
    session_add_notify_script_path=(
        _prefix + 'session_add_notify_script_path'),
    session_delete_notify_script_path=(
        _prefix + 'session_delete_notify_script_path'),
    session_timeout_minutes=_prefix + 'session_timeout_minutes',
    large_file_threshold=_prefix + 'large_file_threshold',
    max_listen_sockets=_prefix + 'max_listen_sockets',
    cgi_maxlen=_prefix + 'cgi_maxlen',
    http_header_max_length=_prefix + 'http_header_max_length',
    enable_ms_public_header=_prefix + 'enable_ms_public_header',
)


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


def http_realm(value):
    value is not None and _setenv('Z_REALM', value)
    return value


def root_wsgi_handler(cfg):
    # Set environment variables
    for k, v in cfg.environment.items():
        os.environ[k] = v

    # set up trusted proxies
    if cfg.trusted_proxies:
        mapped = []
        for name in cfg.trusted_proxies:
            mapped.extend(_name_to_ips(name))

        from ZPublisher import HTTPRequest
        HTTPRequest.trusted_proxies = tuple(mapped)

    # set the maximum number of ConflictError retries
    from ZPublisher import HTTPRequest
    if cfg.max_conflict_retries:
        HTTPRequest.retry_max_count = cfg.max_conflict_retries
    else:
        HTTPRequest.retry_max_count = 3


def _name_to_ips(host, _is_ip=re.compile(r'(\d+\.){3}').match):
    """Map a name *host* to the sequence of its ip addresses.

    use *host* itself (as sequence) if it already is an ip address.
    Thus, if only a specific interface on a host is trusted,
    identify it by its ip (and not the host name).
    """
    if _is_ip(host):
        return [host]
    return gethostbyaddr(host)[2]


def handleWSGIConfig(cfg, multihandler):
    handlers = {}
    for name, value in globals().items():
        if not name.startswith('_'):
            handlers[name] = value
    return multihandler(handlers)
