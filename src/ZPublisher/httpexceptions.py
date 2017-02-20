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

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        environ['Zope2.httpexceptions'] = self
        try:
            return self.application(environ, start_response)
        except HTTPException as exc:
            return exc(environ, start_response)
        except Exception as exc:
            return self.catch_all_response(exc)(environ, start_response)

    def catch_all_response(self, exc):
        response = InternalError()
        response.detail = repr(exc)
        return response


def main(app, global_conf=None):
    return HTTPExceptionHandler(app)
