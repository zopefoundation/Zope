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
"""Image object that is stored in a file"""

__version__='$Revision: 1.4 $'[11:-2]

from OFS.content_types import guess_content_type
from Globals import package_home
from Common import rfc1123_date
from string import rfind, split
from DateTime import DateTime
from time import time
from os import stat
import Acquisition


class ImageFile(Acquisition.Explicit):
    """Image objects stored in external files."""

    def __init__(self,path,_prefix=None):
        if _prefix is None: _prefix=SOFTWARE_HOME
        elif type(_prefix) is not type(''):
            _prefix=package_home(_prefix)
        path='%s/%s' % (_prefix, path)
        self.path=path

        file=open(path, 'rb')
        data=file.read()
        file.close()
        content_type, enc=guess_content_type(path, data)
        if content_type:
            self.content_type=content_type
        else:
            self.content_type='image/%s' % path[rfind(path,'.')+1:]
        self.__name__=path[rfind(path,'/')+1:]
        self.lmt=float(stat(path)[8]) or time()
        self.lmh=rfc1123_date(self.lmt)

    def _init_headers(self, request, response):
#        Waaa... trying to cache aggressively seems to cause problems :(
#
#        ms=request.get_header('If-Modified-Since', None)
#        if ms is not None:
#            ms=split(ms, ';')[0]
#            mst=DateTime(ms).timeTime()
#            if mst >= self.lmt:
#                response.setStatus(304)
#                return response
#        response.setHeader('Expires', rfc1123_date(time()+86400.0))
        response.setHeader('Content-Type', self.content_type)
#        response.setHeader('Last-Modified', self.lmh)

        
    def index_html(self, REQUEST, RESPONSE):
        """Default document"""
        self._init_headers(REQUEST, RESPONSE)
        f=open(self.path,'rb')
        data=f.read()
        f.close()
        return data

    HEAD__roles__=None
    def HEAD(self, REQUEST, RESPONSE):
        """ """
        self._init_headers(self, REQUEST, RESPONSE)
        return ''

    def __len__(self):
        # This is bogus and needed because of the way Python tests truth.
        return 1 

    def __str__(self):
        return '<IMG SRC="%s" ALT="%s">' % (self.__name__, self.title_or_id()) 

