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

from zExceptions import (
    HTTPException,
    InternalError,
)


class HTTPExceptionHandler(object):

    def __init__(self, application, global_conf=None):
        self.application = application
        debug_mode = False
        if global_conf is not None:
            debug_mode = global_conf.get('debug_mode', 'false') == 'true'
        self.debug_mode = debug_mode

    def __call__(self, environ, start_response):
        environ['Zope2.httpexceptions'] = self
        try:
            return self.application(environ, start_response)
        except HTTPException as exc:
            return exc(environ, start_response)
        except Exception as exc:
            if self.debug_mode:
                # In debug mode, let the web server log a real
                # traceback
                raise
            elif environ.get('wsgi.errors') is not None:
                # s. https://www.python.org/dev/peps/pep-0333/#id27
                # Imho the catch all InternalError is the generic error case
                # that should not be handled by the application but
                # rather the WSGI server. This way the error along with
                # the traceback ends up in the configured logs.
                # 'wsgi.errors' must be defined according to PEP-0333
                raise
            return self.catch_all_response(exc)(environ, start_response)

    def catch_all_response(self, exc):
        response = InternalError()
        response.detail = repr(exc)
        return response


def main(app, global_conf=None):
    return HTTPExceptionHandler(app, global_conf=global_conf)
