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

from zope.pagetemplate.pagetemplatefile import DEFAULT_ENCODING


xml_preamble_reg = re.compile(
    br'^<\?xml.*?encoding="(.*?)".*?\?>', re.M)
http_equiv_reg = re.compile(
    br'(<meta\s+[^>]*?http\-equiv[^>]*?content-type.*?>)', re.I | re.M | re.S)
http_equiv_reg2 = re.compile(
    br'charset.*?=.*?(?P<charset>[\w\-]*)', re.I | re.M | re.S)


def encodingFromXMLPreamble(xml, default=DEFAULT_ENCODING):
    """ Extract the encoding from a xml preamble.
        Expects XML content is binary (encoded), otherwise a previous
        transport encoding is meaningless.
        Return 'utf-8' if not available
    """

    match = xml_preamble_reg.match(xml)

    if not match:
        return default
    encoding = match.group(1).lower()
    return encoding.decode('ascii')


def charsetFromMetaEquiv(html):
    """ Return the value of the 'charset' from a html document containing
        <meta http-equiv="content-type" content="text/html; charset=utf8>.
        Expects HTML content is binary (encoded), otherwise a previous
        transport encoding is meaningless.
        Returns None, if not available.
    """

    meta_tag_match = http_equiv_reg.search(html)
    if meta_tag_match:
        meta_tag = meta_tag_match.group(1)

        charset_match = http_equiv_reg2.search(meta_tag)
        if charset_match:
            charset = charset_match.group(1).lower()
            return charset.decode('ascii')

    return None


def convertToUnicode(source, content_type, preferred_encodings):
    """ Convert a binary 'source' to the unicode (text) type.
        Attempts to detect transport encoding from XML and html
        documents, falling back to preferred_encodings.
        Returns (unicode_str, source_encoding).
    """

    if content_type.startswith('text/xml'):
        encoding = encodingFromXMLPreamble(source)
        return source.decode(encoding), encoding

    elif content_type.startswith('text/html'):
        encoding = charsetFromMetaEquiv(source)
        if encoding:
            return source.decode(encoding), encoding

    # Try to detect the encoding by converting it unicode without raising
    # exceptions. There are some smarter Python-based sniffer methods
    # available however we have to check their licenses first before
    # including them into the Zope 2 core

    for enc in preferred_encodings:
        try:
            return source.decode(enc), enc
        except UnicodeDecodeError:
            continue

    # trigger a UnicodeDecodeError so we fail loudly
    return source.decode('utf-8'), 'utf-8'
