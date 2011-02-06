##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""HTTP handler which forces GET requests to return the document source.

Works around current WebDAV clients' failure to implement the
'source-link' feature of the specification.  Uses manage_FTPget().
"""

import os
import posixpath

from ZServer.HTTPServer import zhttp_handler

__version__ = "1.0"


class WebDAVSrcHandler(zhttp_handler):

    def get_environment(self, request):
        """Munge the request to ensure that we call manage_FTPGet."""
        env = zhttp_handler.get_environment(self, request)

        # Set a flag to indicate this request came through the WebDAV source
        # port server.
        env['WEBDAV_SOURCE_PORT'] = 1

        if env['REQUEST_METHOD'] == 'GET':
            path_info = env['PATH_INFO']
            if os.sep != '/':
                path_info =  path_info.replace(os.sep, '/')
            path_info = posixpath.join(path_info, 'manage_DAVget')
            path_info = posixpath.normpath(path_info)
            env['PATH_INFO'] = path_info

        # Workaround for lousy WebDAV implementation of M$ Office 2K.
        # Requests for "index_html" are *sometimes* send as "index_html."
        # We check the user-agent and remove a trailing dot for PATH_INFO
        # and PATH_TRANSLATED

        if env.get("HTTP_USER_AGENT", "").find(
            "Microsoft Data Access Internet Publishing Provider") > -1:
            if env["PATH_INFO"][-1] == '.':
                env["PATH_INFO"] = env["PATH_INFO"][:-1]

            if env["PATH_TRANSLATED"][-1] == '.':
                env["PATH_TRANSLATED"] = env["PATH_TRANSLATED"][:-1]

        return env
