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

"""The webdav package provides WebDAV class 1 functionality within
   the Zope environment. Based on RFC 2518."""

__version__='$Revision: 1.1 $'[11:-2]



# Hacks to inject WebDAV support into standard Zope classes.
from NullResource import NullResource

def folder__getitem__(self, key):
    if hasattr(self, 'REQUEST'):
        method=self.REQUEST.get('REQUEST_METHOD', 'GET')
        if not method in ('GET', 'POST'):
            return NullResource(self, key).__of__(self)
    raise KeyError, key

def document_put(self, REQUEST, RESPONSE):
    """Handle HTTP PUT requests."""
    self.init_headers(RESPONSE)
    type=REQUEST.get_header('content-type', None)
    body=REQUEST.get('BODY', '')
    self._validateProxy(REQUEST)
    self.munge(body)
    self.on_update()
    RESPONSE.setStatus(204)
    return RESPONSE

def image_put(self, REQUEST, RESPONSE):
    """Handle HTTP PUT requests"""
    self.init_headers(RESPONSE)
    type=REQUEST.get_header('content-type', None)
    body=REQUEST.get('BODY', '')
    if type is None:
        type, enc=mimetypes.guess_type(self.id())
    if type is None:
        if content_types.find_binary(body) >= 0:
            type='application/octet-stream'
        else: type=content_types.text_type(body)
    type=lower(type)
    self.update_data(body, type)
    RESPONSE.setStatus(204)
    return RESPONSE






import OFS.SimpleItem, Resource
class Item(OFS.SimpleItem.Item, Resource.Resource):
    pass
Item.__module__='OFS.SimpleItem'
OFS.SimpleItem.Item=Item

class Item_w__name__(OFS.SimpleItem.Item_w__name__, Resource.Resource):
    pass
Item_w__name__.__module__='OFS.SimpleItem'
OFS.SimpleItem.Item_w__name__=Item_w__name__

import OFS.Folder, Collection
class Folder(OFS.Folder.Folder, Collection.Collection):
    pass
Folder.__module__='OFS.Folder'
OFS.Folder.Folder=Folder
OFS.Folder.Folder.__getitem__=folder__getitem__

import OFS.DTMLDocument, OFS.DTMLMethod, OFS.Image
OFS.DTMLMethod.DTMLMethod.PUT=document_put
OFS.DTMLDocument.DTMLDocument.PUT=document_put
OFS.Image.Image.PUT=image_put
OFS.Image.File.PUT=image_put
