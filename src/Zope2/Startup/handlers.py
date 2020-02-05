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
from socket import gethostbyaddr

import ipaddress


def _setenv(name, value):
    if isinstance(value, str):
        os.environ[name] = value
    else:
        os.environ[name] = repr(value)


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


def enable_ms_public_header(value):
    import webdav
    webdav.enable_ms_public_header = value


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
    from ZPublisher.HTTPRequest import HTTPRequest
    if cfg.max_conflict_retries:
        HTTPRequest.retry_max_count = cfg.max_conflict_retries
    else:
        HTTPRequest.retry_max_count = 3


def _name_to_ips(host):
    """Map a name *host* to the sequence of its IP addresses.

    Use *host* itself (as sequence) if it already is an IP address.
    Thus, if only a specific interface on a host is trusted,
    identify it by its IP (and not the host name).
    """
    if isinstance(host, bytes):
        host = host.decode('utf-8')
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return gethostbyaddr(host)[2]
    return [str(ip)]


def handleWSGIConfig(cfg, multihandler):
    handlers = {}
    for name, value in globals().items():
        if not name.startswith('_'):
            handlers[name] = value
    return multihandler(handlers)
