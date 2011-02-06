##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""The webdav package provides WebDAV capability for common Zope objects.

   Current WebDAV support in Zope provides for the correct handling of HTTP
   GET, HEAD, POST, PUT, DELETE, OPTIONS, TRACE, PROPFIND, PROPPATCH, MKCOL,
   COPY and MOVE methods, as appropriate for the object that is the target
   of the operation. Objects which do not support a given operation should
   respond appropriately with a "405 Method Not Allowed" response.

   Note that the ability of a Zope installation to support WebDAV HTTP methods
   depends on the willingness of the web server to defer handling of those
   methods to the Zope process. In most cases, servers will allow the process
   to handle any request, so the Zope portion of your url namespace may well
   be able to handle WebDAV operations even though your web server software
   is not WebDAV-aware itself. Zope installations which use bundled server
   implementations such as ZopeHTTPServer or ZServer should fully support
   WebDAV functions.


   References:

   [WebDAV] Y. Y. Goland, E. J. Whitehead, Jr., A. Faizi, S. R. Carter, D.
   Jensen, "HTTP Extensions for Distributed Authoring - WebDAV." RFC 2518.
   Microsoft, U.C. Irvine, Netscape, Novell.  February, 1999."""

__version__='$Revision: 1.7 $'[11:-2]

enable_ms_author_via = False
enable_ms_public_header = False
