##############################################################################
#
# Copyright (c) 2023 Zope Foundation and Contributors.
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
""" ``PasteDeploy`` filters also known as WSGI middleware.

`The WSGI architecture <https://peps.python.org/pep-3333>`_
consists of a WSGI server, a WSGI application and optionally
WSGI middleware in between.
The server listens for HTTP requests, describes an incoming
request via a WSGI environment, calls the application with
this environment and the function ``start_response`` and sends the
response to the client.
The application is a callable with parameters *environ* and
*start_response*. It processes the request, calls *start_response*
with the response headers and returns an iterable producing the response
body.
A middleware component takes a (base) application and returns an
(enhanced) application.

``PasteDeploy`` calls a middleware component a "filter".
In order to be able to provide parameters, filters are configured
via filter factories. ``paste.deploy`` knows two filter factory types:
``filter_factory`` and ``filter_app_factory``.
A filter_factory has signature ``global_conf, **local_conf`` and
returns a filter (i.e. a function transforming an application into
an application),
a filter_app_factory has signature ``app, global_conf, **local_conf``
and returns the enhanced application directly.
For details see the ``PasteDeploy`` documentation linked from
its PyPI page.

The main content of this module are filter factory definitions.
They are identified by a `filter_` prefix.
Their factory type is determined by the signature.
"""


def filter_content_length(app, global_conf):
    """Honor a ``Content-Length`` header.

    Use this filter if the WSGI server does not follow
    `Note 1 regarding the WSGI input stream
    <https://peps.python.org/pep-3333/#input-and-error-streams>`_
    (such as the ``simple_server`` of Python's ``wsgiref``)
    or violates
    `section 6.3 of RFC 7230
    <https://datatracker.ietf.org/doc/html/rfc7230#section-6.3>`_.
    """
    def enhanced_app(env, start_response):
        wrapped = None
        content_length = env.get("CONTENT_LENGTH")
        if content_length:
            env["wsgi.input"] = wrapped = LimitedFileReader(
                env["wsgi.input"], int(content_length))
        try:
            # Note: this does not special case ``wsgiref.util.FileWrapper``
            # or other similar optimazations
            yield from app(env, start_response)
        finally:
            if wrapped is not None:
                wrapped.discard_remaining()

    return enhanced_app


class LimitedFileReader:
    """File wrapper emulating EOF."""

    # attributes to be delegated to the file
    DELEGATE = {"close", "closed", "fileno", "mode", "name"}

    BUFSIZE = 1 << 14

    def __init__(self, fp, limit):
        """emulate EOF after *limit* bytes have been read.

        *fp* is a binary file like object.
        """
        self.fp = fp
        assert limit >= 0
        self.limit = limit

    def _enforce_limit(self, size):
        limit = self.limit
        return limit if size is None or size < 0 else min(size, limit)

    def read(self, size=-1):
        data = self.fp.read(self._enforce_limit(size))
        self.limit -= len(data)
        return data

    def readline(self, size=-1):
        data = self.fp.readline(self._enforce_limit(size))
        self.limit -= len(data)
        return data

    def __iter__(self):
        return self

    def __next__(self):
        data = self.readline()
        if not data:
            raise StopIteration()
        return data

    def discard_remaining(self):
        while self.read(self.BUFSIZE):
            pass

    def __getattr__(self, attr):
        if attr not in self.DELEGATE:
            raise AttributeError(attr)
        return getattr(self.fp, attr)
