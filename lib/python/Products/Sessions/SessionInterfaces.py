############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
############################################################################
"""

Session APIs

  See Also

    - "Transient Object API":../../Transience/Help/TransienceInterfaces.py

"""

import Interface

class BrowserIdManagerInterface(
    Interface.Base
    ):
    """
    Zope Browser Id Manager interface.

    A Zope Browser Id Manager is responsible for assigning ids to site
    visitors, and for servicing requests from Session Data Managers
    related to the browser id.
    """
    def encodeUrl(url, style='querystring'):
        """
        Encodes a provided URL with the current request's browser id
        and returns the result.  Two forms of URL-encoding are supported:
        'querystring' and 'inline'.  'querystring' is the default.

        If the 'querystring' form is used, the browser id name/value pair
        are postfixed onto the URL as a query string.  If the 'inline'
        form is used, the browser id name/value pair are prefixed onto
        the URL as the first two path segment elements.

        For example:

         The call encodeUrl('http://foo.com/amethod', style='querystring')
         might return 'http://foo.com/amethod?_ZopeId=as9dfu0adfu0ad'.

         The call encodeUrl('http://foo.com/amethod, style='inline')
         might return 'http://foo.com/_ZopeId/as9dfu0adfu0ad/amethod'.

        Permission required: Access contents information

        Raises:  BrowserIdManagerErr.  If there is no current browser id.
        """

    def getBrowserIdName():
        """
        Returns a string with the name of the cookie/form variable which is
        used by the current browser id manager as the name to look up when
        attempting to obtain the browser id value.  For example, '_ZopeId'.

        Permission required: Access contents information
        """

    def getBrowserId(create=1):
        """
        If create=0, returns a the current browser id or None if there
        is no browser id associated with the current request.  If create=1,
        returns the current browser id or a newly-created browser id if
        there is no browser id associated with the current request.  This
        method is useful in conjunction with getBrowserIdName if you wish to
        embed the browser-id-name/browser-id combination as a hidden value in
        a POST-based form.  The browser id is opaque, has no business meaning,
        and its length, type, and composition are subject to change.

        Permission required: Access contents information

        Raises:  BrowserIdManagerErr.  If ill-formed browser id
        is found in REQUEST.
        """

    def hasBrowserId():
        """
        Returns true if there is a browser id for this request.

        Permission required: Access contents information
        """

    def isBrowserIdNew():
        """
        Returns true if browser id is 'new'.  A browser id is 'new'
        when it is first created and the client has therefore not sent it
        back to the server in any request.

        Permission required: Access contents information

        Raises:  BrowserIdManagerErr.  If there is no current browser id.
        """

    def isBrowserIdFromForm():
        """
        Returns true if browser id comes from a form variable (query
        string or post).

        Permission required: Access contents information

        Raises:  BrowserIdManagerErr.  If there is no current browser id.
        """

    def isBrowserIdFromCookie():
        """
        Returns true if browser id comes from a cookie.

        Permission required: Access contents information

        Raises:  BrowserIdManagerErr.  If there is no current browser id.
        """

    def flushBrowserIdCookie():
        """
        Deletes the browser id cookie from the client browser, iff the
        'cookies' browser id namespace is being used.

        Permission required: Access contents information

        Raises:  BrowserIdManagerErr.  If the 'cookies' namespace isn't
        a browser id namespace at the time of the call.
        """

    def setBrowserIdCookieByForce(bid):
        """
        Sets the browser id cookie to browser id 'bid' by force.
        Useful when you need to 'chain' browser id cookies across domains
        for the same user (perhaps temporarily using query strings).

        Permission required: Access contents information

        Raises:  BrowserIdManagerErr.  If the 'cookies' namespace isn't
        a browser id namespace at the time of the call.
        """

    def getHiddenFormField():
        """
        Returns a string in the form:

        <input type="hidden" name="_ZopeId" value="H7HJGYUFGFyHKH*">

        Where the name and the value represent the current browser id
        name and current browser id.
        """

class SessionDataManagerInterface(
    Interface.Base
    ):
    """
    Zope Session Data Manager interface.

    A Zope Session Data Manager is responsible for maintaining Session
    Data Objects, and for servicing requests from application code
    related to Session Data Objects.  It also communicates with a Browser
    Id Manager to provide information about browser ids.
    """
    def getBrowserIdManager():
        """
        Returns the nearest acquirable browser id manager.

        Raises SessionDataManagerErr if no browser id manager can be found.

        Permission required: Access session data
        """

    def getSessionData(create=1):
        """
        Returns a Session Data Object associated with the current
        browser id.  If there is no current browser id, and create is true,
        returns a new Session Data Object.  If there is no current
        browser id and create is false, returns None.

        Permission required: Access session data
        """

    def hasSessionData():
        """
        Returns true if a Session Data Object associated with the
        current browser id is found in the Session Data Container.  Does
        not create a Session Data Object if one does not exist.

        Permission required: Access session data
        """

    def getSessionDataByKey(key):
        """
        Returns a Session Data Object associated with 'key'.  If there is
        no Session Data Object associated with 'key' return None.

        Permission required: Access arbitrary user session data
        """

class SessionDataManagerErr(Interface.Base):
    """
    Error raised during some session data manager operations, as
    explained in the API documentation of the Session Data Manager.

    This exception may be caught in PythonScripts.  A successful
    import of the exception for PythonScript use would need to be::

       from Products.Sessions import SessionDataManagerErr
    """

class BrowserIdManagerErr(Interface.Base):
    """
    Error raised during some browser id manager operations, as
    explained in the API documentation of the Browser Id Manager.

    This exception may be caught in PythonScripts.  A successful
    import of the exception for PythonScript use would need to be::

       from Products.Sessions import BrowserIdManagerErr
    """
