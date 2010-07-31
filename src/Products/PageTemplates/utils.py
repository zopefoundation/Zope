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
"""Some helper methods
"""

import re 

xml_preamble_reg = re.compile(r'^<\?xml.*?encoding="(.*?)".*?\?>', re.M)
http_equiv_reg = re.compile(r'(<meta\s+[^>]*?http\-equiv[^>]*?content-type.*?>)', re.I|re.M|re.S)
http_equiv_reg2 = re.compile(r'charset.*?=.*?(?P<charset>[\w\-]*)', re.I|re.M|re.S)

def encodingFromXMLPreamble(xml):
    """ Extract the encoding from a xml preamble.
        Return 'utf-8' if not available
    """

    mo = xml_preamble_reg.match(xml)

    if not mo:
        return 'utf-8'
    else:
        return mo.group(1).lower()


def charsetFromMetaEquiv(html):                                    
    """ Return the value of the 'charset' from a html document
        containing <meta http-equiv="content-type" content="text/html; charset=utf8>.
        Returns None, if not available.
    """

    # first check for the <meta...> tag
    mo = http_equiv_reg.search(html)
    if mo:
        # extract the meta tag
        meta = mo.group(1)

        # search for the charset value
        mo = http_equiv_reg2.search(meta)
        if mo:
            # return charset 
            return mo.group(1).lower()

    return None


def convertToUnicode(source, content_type, preferred_encodings):
    """ Convert 'source' to unicode.
        Returns (unicode_str, source_encoding).
    """

    if content_type.startswith('text/xml'):
        encoding = encodingFromXMLPreamble(source)
        return unicode(source, encoding), encoding  

    elif content_type.startswith('text/html'):
        encoding = charsetFromMetaEquiv(source)
        if encoding:
            return unicode(source, encoding), encoding  

    # Try to detect the encoding by converting it unicode without raising
    # exceptions. There are some smarter Python-based sniffer methods
    # available however we have to check their licenses first before
    # including them into the Zope 2 core

    for enc in preferred_encodings:
        try:
            return unicode(source, enc), enc
        except UnicodeDecodeError:
                continue

    return unicode(source), None
