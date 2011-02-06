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



class Request:

    """

    The request object encapsulates all of the information regarding
    the current request in Zope.  This includes, the input headers,
    form data, server data, and cookies.

    The request object is a mapping object that represents a
    collection of variable to value mappings.  In addition, variables
    are divided into five categories:

      - Environment variables

          These variables include input headers, server data, and
          other request-related data.  The variable names are as <a
          href="http://hoohoo.ncsa.uiuc.edu/cgi/env.html">specified</a>
          in the <a
          href="http://hoohoo.ncsa.uiuc.edu/cgi/interface.html">CGI
          specification</a>

      - Form data

          These are data extracted from either a URL-encoded query
          string or body, if present.

      - Cookies

          These are the cookie data, if present.

      - Lazy Data

          These are callables which are deferred until explicitly
          referenced, at which point they are resolved (called) and
          the result stored as "other" data, ie regular request data.

          Thus, they are "lazy" data items.  An example is SESSION objects.

          Lazy data in the request may only be set by the Python
          method set_lazy(name,callable) on the REQUEST object.  This
          method is not callable from DTML or through the web.

      - Other

          Data that may be set by an application object.

    The request object may be used as a mapping object, in which case
    values will be looked up in the order: environment variables,
    other variables, form data, and then cookies.

    These special variables are set in
    the Request:

      'PARENTS' -- A list of the objects traversed to get to the
      published object. So, 'PARENTS[0]' would be the ancestor of
      the published object.

      'REQUEST' -- The Request object.

      'RESPONSE' -- The Response object.

      'PUBLISHED' -- The actual object published as a result of
      url traversal.

      'URL' -- The URL of the Request without query string.

      *URLn* -- 'URL0' is the same as 'URL'. 'URL1' is the same as
      'URL0' with the last path element removed. 'URL2' is the same
      as 'URL1' with the last element removed. Etcetera.

        For example if URL='http://localhost/foo/bar', then
        URL1='http://localhost/foo' and URL2='http://localhost'.

      *URLPATHn* -- 'URLPATH0' is the path portion of 'URL',
      'URLPATH1' is the path portion of 'URL1', and so on.

        For example if URL='http://localhost/foo/bar', then
        URLPATH1='/foo' and URLPATH2='/'.

      *BASEn* -- 'BASE0' is the URL up to but not including the Zope
      application object. 'BASE1' is the URL of the Zope application
      object. 'BASE2' is the URL of the Zope application object with
      an additional path element added in the path to the published
      object. Etcetera.

        For example if URL='http://localhost/Zope.cgi/foo/bar', then
        BASE0='http://localhost', BASE1='http://localhost/Zope.cgi',
        and BASE2='http://localhost/Zope.cgi/foo'.

      *BASEPATHn* -- 'BASEPATH0' is the path portion of 'BASE0',
      'BASEPATH1' is the path portion of 'BASE1', and so on.
      'BASEPATH1' is the externally visible path to the root Zope
      folder, equivalent to CGI's 'SCRIPT_NAME', but virtual-host aware.

        For example if URL='http://localhost/Zope.cgi/foo/bar', then
        BASEPATH0='/', BASEPATH1='/Zope.cgi', and BASEPATH2='/Zope.cgi/foo'.

    """


    def set(name, value):
        """

        Create a new name in the REQUEST object and assign it a value.
        This name and value is stored in the 'Other' category.

        Permission -- Always available

        """


    def get_header(name, default=None):
        """

        Return the named HTTP header, or an optional default argument
        or None if the header is not found. Note that both original
        and CGI header names without the leading 'HTTP_' are
        recognized, for example, 'Content-Type', 'CONTENT_TYPE' and
        'HTTP_CONTENT_TYPE' should all return the Content-Type header,
        if available.

        Permission -- Always available

        """


    def has_key(key):
        """

        Returns a true value if the REQUEST object contains key,
        returns a false value otherwise.

        Permission -- Always available

        """


    def keys():
        """

        Returns a sorted sequence of all keys in the REQUEST object.

        Permission -- Always available

        """

    def items():
        """

        Returns a sequence of (key, value) tuples for all the keys in
        the REQUEST object.

        Permission -- Always available

        """

    def values():
        """

        Returns a sequence of values for all the keys in the REQUEST
        object.

        Permission -- Always available

        """

    def setServerURL(protocol=None, hostname=None, port=None):
        """

        Sets the specified elements of 'SERVER_URL', also affecting
        'URL', 'URLn', 'BASEn', and 'absolute_url()'.

        Provides virtual hosting support.

        Permission -- Always available

        """

    def setVirtualRoot(path, hard=0):
        """

        Alters 'URL', 'URLn', 'URLPATHn', 'BASEn', 'BASEPATHn', and
        'absolute_url()' so that the current object has path 'path'.
        If 'hard' is true, 'PARENTS' is emptied.

        Provides virtual hosting support.  Intended to be called from
        publishing traversal hooks.

        Permission -- Always available

        """

    def text():
        """
        Returns information about the request as text. This is useful
        for debugging purposes. The returned text lists form contents,
        cookies, special variables, and evironment variables.

        Permissions -- Always available
        """
