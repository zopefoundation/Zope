############################################################################
# 
# Zope Public License (ZPL) Version 1.1
# -------------------------------------
# 
# Copyright (c) Zope Corporation.  All rights reserved.
# 
# This license has been certified as open source.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Zope Corporation 
#      for use in the Z Object Publishing Environment
#      (http://www.zope.com/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 4. Names associated with Zope or Zope Corporation must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Zope Corporation.
# 
# 5. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Zope Corporation
#      for use in the Z Object Publishing Environment
#      (http://www.zope.com/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 6. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY ZOPE CORPORATION ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL ZOPE CORPORATION OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Zope Corporation and
# many individuals on behalf of Zope Corporation.  Specific
# attributions are listed in the accompanying credits file.
#
############################################################################
"""

Session API

  See Also

    - "Programming with the Session API":sessionapi-prog.stx

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
    related to the browser token.
    """
    def encodeUrl(self, url):
        """
        Encodes a provided URL with the current request's browser token
        and returns the result.  For example, the call
        encodeUrl('http://foo.com/amethod') might return
        'http://foo.com/amethod?_ZopeId=as9dfu0adfu0ad'.

        Permission required: Access contents information

        Raises:  BrowserIdManagerErr.  If there is no current session token.
        """

    def getTokenKey(self):
        """
        Returns a string with the name of the cookie/form variable which is
        used by the current browser id manager as the name to look up when
        attempting to obtain the browser token value.  For example, '_ZopeId'.

        Permission required: Access contents information
        """

    def getToken(self, create=1):
        """
        If create=0, returns a the current browser token or None if there
        is no browser token associated with the current request.  If create=1,
        returns the current browser token or a newly-created browser token if
        there is no browser token associated with the current request.  This
        method is useful in conjunction with getTokenKey if you wish to embed
        the token-key/token combination as a hidden value in a POST-based
        form.  The browser token is opaque, has no business meaning, and its
        length, type, and composition are subject to change.

        Permission required: Access contents information

        Raises:  BrowserIdManagerErr.  If ill-formed browser token
        is found in REQUEST.
        """

    def hasToken(self):
        """
        Returns true if there is a browser token for this request.

        Permission required: Access contents information
        """

    def isTokenNew(self):
        """
        Returns true if browser token is 'new'.  A browser token is 'new'
        when it is first created and the client has therefore not sent it
        back to the server in any request.  

        Permission required: Access contents information

        Raises:  BrowserIdManagerErr.  If there is no current browser token.
        """

    def isTokenFromForm(self):
        """
        Returns true if browser token comes from a form variable (query
        string or post).

        Permission required: Access contents information

        Raises:  BrowserIdManagerErr.  If there is no current browser token.
        """

    def isTokenFromCookie(self):
        """
        Returns true if browser token comes from a cookie.

        Permission required: Access contents information

        Raises:  BrowserIdManagerErr.  If there is no current browser token.
        """

    def flushTokenCookie(self):
        """
        Deletes the token cookie from the client browser, iff the
        'cookies' token key namespace is being used.
        
        Permission required: Access contents information

        Raises:  BrowserIdManagerErr.  If the 'cookies' namespace isn't
        a token key namespace at the time of the call.
        """

class SessionDataManagerInterface(
    Interface.Base
    ):
    """
    Zope Session Data Manager interface.

    A Zope Session Data Manager is responsible for maintaining Session
    Data Objects, and for servicing requests from application code
    related to Session Data Objects.  It also communicates with a Browser
    Id Manager to provide information about browser tokens.
    """
    def getBrowserIdManager(self):
        """
        Returns the nearest acquirable browser id manager.

        Raises SessionDataManagerErr if no browser id manager can be found.

        Permission required: Access session data
        """

    def getSessionData(self, create=1):
        """
        Returns a Session Data Object associated with the current
        browser token.  If there is no current token, and create is true,
        returns a new Session Data Object.  If there is no current
        token and create is false, returns None.

        Permission required: Access session data
        """

    def hasSessionData(self):
        """
        Returns true if a Session Data Object associated with the
        current browser token is found in the Session Data Container.  Does
        not create a Session Data Object if one does not exist.

        Permission required: Access session data
        """

    def getSessionDataByKey(self, key):
        """
        Returns a Session Data Object associated with 'key'.  If there is
        no Session Data Object associated with 'key' return None.

        Permission required: Access arbitrary user session data
        """


