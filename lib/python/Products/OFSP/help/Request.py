##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
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
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
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
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################



class Request:

    """

    The request object encapsulates all of the information regarding
    the current request in Zope.  This includes, the input headers,
    form data, server data, and cookies.

    The request object is a mapping object that represents a
    collection of variable to value mappings.  In addition, variables
    are divided into four categories:

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

      - Other

          Data that may be set by an application object.

    The request object may be used as a mapping object, in which case
    values will be looked up in the order: environment variables,
    other variables, form data, and then cookies.

    Special Variables

      These special variables are set in the Request

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

        Permission - Always available
        
        """

        
    def get_header(name, default=None):
        """

        Return the named HTTP header, or an optional default argument
        or None if the header is not found. Note that both original
        and CGI-ified header names are recognized,
        e.g. 'Content-Type', 'CONTENT_TYPE' and 'HTTP_CONTENT_TYPE'
        should all return the Content-Type header, if available.

        Permission - Always available
        
        """


    def has_key(key):
        """

        Returns a true value if the REQUEST object contains key,
        returns a false value otherwise.

        Permission - Always available
        
        """


    def keys():
        """

        Returns a sorted sequence of all keys in the REQUEST object.

        Permission - Always available
        
        """

    def items():
        """

        Returns a sequence of (key, value) tuples for all the keys in
        the REQUEST object.

        Permission - Always available
        
        """

    def values():
        """

        Returns a sequence of values for all the keys in the REQUEST
        object.

        Permission - Always available
        
        """

    def setServerURL(protocol=None, hostname=None, port=None):
        """

        Sets the specified elements of 'SERVER_URL', also affecting
        'URL', 'URLn', 'BASEn', and 'absolute_url()'.

        Provides virtual hosting support.

        Permission - Always available

        """

    def setVirtualRoot(path, hard=0):
        """

        Alters 'URL', 'URLn', 'URLPATHn', 'BASEn', 'BASEPATHn', and
        'absolute_url()' so that the current object has path 'path'.
        If 'hard' is true, 'PARENTS' is emptied.

        Provides virtual hosting support.  Intended to be called from
        publishing traversal hooks.

        Permission - Always available

        """






