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
"""A utility module for content-type handling."""
__version__='$Revision: 1.14 $'[11:-2]

from string import split, strip, lower, find
import re, mimetypes


find_binary=re.compile('[\0-\7]').search

def text_type(s):
    # Yuk. See if we can figure out the type by content.
    if (lower(strip(s)[:6]) == '<html>' or find(s, '</') > 0):
        return 'text/html'
    return 'text/plain'



# This gives us a hook to add content types that
# aren't currently listed in the mimetypes module.
_addtypes=(
    ('.mp3', 'audio/mpeg'),
    ('.ra', 'audio/x-pn-realaudio'),
    ('.pdf', 'application/pdf'),
    ('.c', 'text/plain'),
    ('.bat', 'text/plain'),
    ('.h', 'text/plain'),
    ('.pl', 'text/plain'),
    ('.ksh', 'text/plain'),
    ('.ram', 'application/x-pn-realaudio'),
    ('.cdf', 'application-x-cdf'),
    ('.doc', 'application/msword'),
    ('.dot', 'application/msword'),
    ('.wiz', 'application/msword'),
    ('.xlb', 'application/vnd.ms-excel'),
    ('.xls', 'application/vnd.ms-excel'),
    ('.ppa', 'application/vnd.ms-powerpoint'),
    ('.ppt', 'application/vnd.ms-powerpoint'),
    ('.pps', 'application/vnd.ms-powerpoint'),
    ('.pot', 'application/vnd.ms-powerpoint'),
    ('.pwz', 'application/vnd.ms-powerpoint'),
    ('.eml',   'message/rfc822'),
    ('.nws',   'message/rfc822'),
    ('.mht',   'message/rfc822'),
    ('.mhtml', 'message/rfc822'),
    ('.css', 'text/css'),
    ('.p7c', 'application/pkcs7-mime'),
    ('.p12', 'application/x-pkcs12'),
    ('.pfx', 'application/x-pkcs12'),
    ('.js',  'application/x-javascript'),
    ('.pct', 'image/pict'),
    ('.pic', 'image/pict'),
    ('.pict', 'image/pict'),
    ('.m1v', 'video/mpeg'),
    ('.mpa', 'video/mpeg'),
    ('.vcf', 'text/x-vcard'),
    ('.xml', 'text/xml'),
    ('.xsl', 'text/xsl'),
    ('.xul', 'text/xul'),
    )
for name, val in _addtypes:
    mimetypes.types_map[name]=val

def guess_content_type(name='', body='', default=None):
    # Attempt to determine the content type (and possibly
    # content-encoding) based on an an object's name and
    # entity body.
    type, enc=mimetypes.guess_type(name)
    if type is None:
        if body:
            if find_binary(body) is not None:
                type=default or 'application/octet-stream'
            else:
                type=(default or text_type(body) 
                      or 'text/x-unknown-content-type')
        else:
                type=default or 'text/x-unknown-content-type'
        
    return lower(type), enc and lower(enc) or None

if __name__=='__main__':
    items=mimetypes.types_map.items()
    items.sort()
    for item in items: print "%s:\t%s" % item

