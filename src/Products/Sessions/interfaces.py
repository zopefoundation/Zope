############################################################################
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
############################################################################
""" Session APIs

o See Also

    - "Transient Object API":../../Transience/Help/TransienceInterfaces.py

"""
from zope.interface import Interface

class IBrowserIdManager(Interface):
    """ Zope Browser Id Manager interface.

    A Zope Browser Id Manager is responsible for assigning ids to site
    visitors, and for servicing requests from Session Data Managers
    related to the browser id.
    """
    def hasBrowserId():
        """ Return true if there is a browser id for the current request.

        o Permission required: Access contents information

        o Does *not* raise an error if the request contains a broken
          browser id.
        """

    def getBrowserId(create=1):
        """ Return a browser id for the current request.

        o If create is false, return None if there is no browser id associated
          with the current request.
          
        o If create is true, return a newly-created browser id if
          there is no browser id associated with the current request.
          
        o This method is useful in conjunction with 'getBrowserIdName' if you
          wish to embed the browser-id-name/browser-id combination as a hidden
          value in a POST-based form.
          
        o The browser id is opaque, has no business meaning, and its length,
          type, and composition are subject to change.

        o Permission required: Access contents information

        o Raises BrowserIdManagerErr if an ill-formed browser id
          is found in REQUEST.
        """

    def getBrowserIdName():
        """
        Returns a string with the name of the cookie/form variable which is
        used by the current browser id manager as the name to look up when
        attempting to obtain the browser id value.  For example, '_ZopeId'.

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

    def isBrowserIdFromCookie():
        """ Return true if browser id comes from a cookie.

        o Permission required: Access contents information

        o Raise BrowserIdManagerErr if there is no current browser id.
        """

    def isBrowserIdFromForm():
        """ Return true if browser id comes from a form variable.
        
        o Variable may come from either the query string or a post.

        o Permission required: Access contents information

        o Raise BrowserIdManagerErr if there is no current browser id.
        """

    def isBrowserIdFromUrl():
        """ Return true if browser id comes from a cookie.

        o Permission required: Access contents information

        o Raise BrowserIdManagerErr if there is no current browser id.
        """

    def flushBrowserIdCookie():
        """ Deletes the browser id cookie from the client browser.

        o Permission required: Access contents information

        o Raise BrowserIdManagerErr if the 'cookies' namespace isn't
          a browser id namespace.
        """

    def setBrowserIdCookieByForce(bid):
        """ Sets the browser id cookie to browser id 'bid' by force.

        o Useful when you need to 'chain' browser id cookies across domains
          for the same user (perhaps temporarily using query strings).

        o Permission required: Access contents information

        o Raise BrowserIdManagerErr if the 'cookies' namespace isn't
          a browser id namespace.
        """

    def getHiddenFormField():
        """ Return a string usable as a hidden form field for the browser id.
        
        o String is of the form::

          <input type="hidden" name="_ZopeId" value="H7HJGYUFGFyHKH*" />

        o name and the value represent the current browser id
          name and current browser id.
        """

    def encodeUrl(url, style='querystring'):
        """ Encode a given URL with the current browser id.
        
        o Two forms of URL-encoding are supported: 'querystring' and 'inline'.
        
        o 'querystring' is the default.

        o If the 'querystring' form is used, the browser id name/value pair
          are postfixed onto the URL as a query string.
          
        o If the 'inline' form is used, the browser id name/value pair
          are prefixed onto the URL as the first two path segment elements.

        o For example:

          - The call encodeUrl('http://foo.com/amethod', style='querystring')
            might return 'http://foo.com/amethod?_ZopeId=as9dfu0adfu0ad'.

          - The call encodeUrl('http://foo.com/amethod, style='inline')
            might return 'http://foo.com/_ZopeId/as9dfu0adfu0ad/amethod'.

        o Permission required: Access contents information

        o Raise BrowserIdManagerErr if there is no current browser id.
        """

class BrowserIdManagerErr(ValueError):
    """ Error raised during some browser id manager operations
    
    o See IBrowserIdManager methods.

    o This exception may be caught in PythonScripts.  A successful
      import of the exception for PythonScript use would need to be::

       from Products.Sessions.interfaces import BrowserIdManagerErr
    """

class ISessionDataManager(Interface):
    """ Zope Session Data Manager interface.

    A Zope Session Data Manager is responsible for maintaining Session
    Data Objects, and for servicing requests from application code
    related to Session Data Objects.  It also communicates with a Browser
    Id Manager to provide information about browser ids.
    """
    def getBrowserIdManager():
        """ Return the nearest acquirable browser id manager.

        o Raise SessionDataManagerErr if no browser id manager can be found.

        o Permission required: Access session data
        """

    def getSessionData(create=1):
        """ Return a Session Data Object for the current browser id.
        
        o If there is no current browser id, and create is true,
          return a new Session Data Object.
          
        o If there is no current browser id and create is false, returns None.

        o Permission required: Access session data
        """

    def hasSessionData():
        """ Does a Session Data Object exist for the current browser id?

        o Do not create a Session Data Object if one does not exist.

        o Permission required: Access session data
        """

    def getSessionDataByKey(key):
        """ Return a Session Data Object associated with 'key'.
        
        o If there is no Session Data Object associated with 'key',
          return None.

        o Permission required: Access arbitrary user session data
        """

class SessionDataManagerErr(ValueError):
    """ Error raised during some session data manager operations
    
    o See ISesseionDataManager.

    o This exception may be caught in PythonScripts.  A successful
      import of the exception for PythonScript use would need to be::

       from Products.Sessions.interfaces import SessionDataManagerErr
    """
