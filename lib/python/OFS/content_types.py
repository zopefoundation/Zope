##############################################################################
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
##############################################################################
"""A utility module for content-type handling."""
__version__='$Revision: 1.19 $'[11:-2]

import re, mimetypes


find_binary=re.compile('[\0-\7]').search

def text_type(s):
    # Yuk. See if we can figure out the type by content.
    if (s.strip().lower()[:6] == '<html>' or s.find('</') > 0):
        return 'text/html'

    elif s.strip().startswith('<?xml'):
        return 'text/xml'

    else:
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
    ('.xsl', 'text/xml'),
    ('.xul', 'application/vnd.mozilla.xul+xml'),
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

    return type.lower(), enc and enc.lower() or None

if __name__=='__main__':
    items=mimetypes.types_map.items()
    items.sort()
    for item in items: print "%s:\t%s" % item
