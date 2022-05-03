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

from zExceptions import HTTPException


class HTTPExceptionHandler:

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


def main(app, global_conf=None):
    return HTTPExceptionHandler(app, global_conf=global_conf)
