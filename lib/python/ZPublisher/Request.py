##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################
__version__='$Revision: 1.6 $'[11:-2]

import regex
from string import atoi, atol, join, upper, split, strip, rfind

isCGI_NAME = {
        'SERVER_SOFTWARE' : 1, 
        'SERVER_NAME' : 1, 
        'GATEWAY_INTERFACE' : 1, 
        'SERVER_PROTOCOL' : 1, 
        'SERVER_PORT' : 1, 
        'REQUEST_METHOD' : 1, 
        'PATH_INFO' : 1, 
        'PATH_TRANSLATED' : 1, 
        'SCRIPT_NAME' : 1, 
        'QUERY_STRING' : 1, 
        'REMOTE_HOST' : 1, 
        'REMOTE_ADDR' : 1, 
        'AUTH_TYPE' : 1, 
        'REMOTE_USER' : 1, 
        'REMOTE_IDENT' : 1, 
        'CONTENT_TYPE' : 1, 
        'CONTENT_LENGTH' : 1, 
        }.has_key

hide_key={'HTTP_AUTHORIZATION':1,
          'HTTP_CGI_AUTHORIZATION': 1,
          }.has_key

class Request:
    """\
    Model HTTP request data.
    
    This object provides access to request data.  This includes, the
    input headers, form data, server data, and cookies.

    Request objects are created by the object publisher and will be
    passed to published objects through the argument name, REQUEST.

    The request object is a mapping object that represents a
    collection of variable to value mappings.  In addition, variables
    are divided into four categories:

      - Environment variables

        These variables include input headers, server data, and other
        request-related data.  The variable names are as <a
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

    The form attribute of a request is actually a Field Storage
    object.  When file uploads are used, this provides a richer and
    more complex interface than is provided by accessing form data as
    items of the request.  See the FieldStorage class documentation
    for more details.

    The request object may be used as a mapping object, in which case
    values will be looked up in the order: environment variables,
    other variables, form data, and then cookies.
    """

    def __init__(self,environ,form,stdin):
        self.environ=environ
        self.other=form
        self.stdin=stdin
        have_env=environ.has_key

        b=script=strip(environ['SCRIPT_NAME'])
        while b and b[-1]=='/': b=b[:-1]
        p = rfind(b,'/')
        if p >= 0: b=b[:p+1]
        else: b=''
        while b and b[0]=='/': b=b[1:]
        
        if have_env('SERVER_URL'):
             server_url=strip(environ['SERVER_URL'])
        else:
             if have_env('HTTPS') and (
                 environ['HTTPS'] == "on" or environ['HTTPS'] == "ON"):
                 server_url='https://'
             elif (have_env('SERVER_PORT_SECURE') and 
                   environ['SERVER_PORT_SECURE'] == "1"):
                 server_url='https://'
             else: server_url='http://'

             if have_env('HTTP_HOST'):
                 server_url=server_url+strip(environ['HTTP_HOST'])
             else:
                 server_url=server_url+strip(environ['SERVER_NAME'])
                 server_port=environ['SERVER_PORT']
                 if server_port!='80': server_url=server_url+':'+server_port

        if server_url[-1:]=='/': server_url=server_url[:-1]
                        
        self.base="%s/%s" % (server_url,b)
        while script[:1]=='/': script=script[1:]
        if script: self.script="%s/%s" % (server_url,script)
        else:  self.script=server_url

    def get_header(self, name, default=None):
        """Return the named HTTP header, or an optional default
        argument or None if the header is not found. Note that
        both original and CGI-ified header names are recognized,
        e.g. 'Content-Type', 'CONTENT_TYPE' and 'HTTP_CONTENT_TYPE'
        should all return the Content-Type header, if available.
        """
        environ=self.environ
        name=upper(join(split(name,"-"),"_"))
        val=environ.get(name, None)
        if val is not None:
            return val
        if name[:5] != 'HTTP_':
            name='HTTP_%s' % name
        return environ.get(name, default)

    def __setitem__(self,key,value):
        """Set application variables

        This method is used to set a variable in the requests "other"
        category.
        """
        self.other[key]=value

    set=__setitem__

    def __getitem__(self,key,
                    default=isCGI_NAME, # Any special internal marker will do
                    URLmatch=regex.compile('URL[0-9]$').match,
                    BASEmatch=regex.compile('BASE[0-9]$').match,
                    ):
        """Get a variable value

        Return a value for the required variable name.
        The value will be looked up from one of the request data
        categories. The search order is environment variables,
        other variables, form data, and then cookies. 
        
        """ #"
        other=self.other
        if other.has_key(key):
            if key=='REQUEST': return self
            return other[key]

        if key[:1]=='U' and URLmatch(key) >= 0 and other.has_key('URL'):
            n=ord(key[3])-ord('0')
            URL=other['URL']
            for i in range(0,n):
                l=rfind(URL,'/')
                if l >= 0: URL=URL[:l]
                else: raise KeyError, key
            other[key]=URL
            return URL

        if isCGI_NAME(key) or key[:5] == 'HTTP_':
            environ=self.environ
            if environ.has_key(key) and (not hide_key(key)):
                return environ[key]
            return ''

        if key=='REQUEST': return self

        if key[:1]=='B' and BASEmatch(key) >= 0 and other.has_key('URL'):
            n=ord(key[4])-ord('0')
            if n:
                v=self.script
                while v[-1:]=='/': v=v[:-1]
                v=join([v]+self.steps[:n-1],'/')
            else:
                v=self.base
                while v[-1:]=='/': v=v[:-1]
            other[key]=v
            return v

        if default is not isCGI_NAME: # Check marker
            return default

        raise KeyError, key

    __getattr__=get=__getitem__

    def has_key(self,key):
        return self.get(key, Request) is not Request

    def keys(self):
        keys = {}
        for key in self.environ.keys():
            if (isCGI_NAME(key) or key[:5] == 'HTTP_') and \
               (not hide_key(key)):
                    keys[key] = 1
        keys.update(self.other)
        lasturl = ""
        for n in "0123456789":
            key = "URL%s"%n
            try:
                if lasturl != self[key]:
                    keys[key] = 1
                    lasturl = self[key]
                else:
                    break
            except KeyError:
                pass
        for n in "0123456789":
            key = "BASE%s"%n
            try:
                if lasturl != self[key]:
                    keys[key] = 1
                    lasturl = self[key]
                else:
                    break
            except KeyError:
                pass
        return keys.keys()

    def items(self):
        result = []
        for k in self.keys():
            result.append((k, self.get(k)))
        return result

    def __str__(self):

        def str(self,name):
            dict=getattr(self,name)
            data=[]
            for key, val in dict.items():
                if not hide_key(key):
                    data.append('%s: %s' % (key, `val`))
            return "%s:\n\t%s\n\n" % (name, join(data, '\n\t'))
            
        return "%s\n%s\n" % (str(self,'form'), str(self,'environ'))

    __repr__=__str__



