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
"""A utility module for content-type handling.

$Id$
"""
import mimetypes
import os.path
import re


find_binary = re.compile('[\0-\7]').search

def text_type(s):
    # Yuk. See if we can figure out the type by content.
    if (s.strip().lower()[:6] == '<html>' or s.find('</') > 0):
        return 'text/html'

    elif s.strip().startswith('<?xml'):
        return 'text/xml'

    else:
        return 'text/plain'


def guess_content_type(name='', body='', default=None):
    # Attempt to determine the content type (and possibly
    # content-encoding) based on an an object's name and
    # entity body.
    type, enc = mimetypes.guess_type(name)
    if type is None:
        if body:
            if find_binary(body) is not None:
                type = default or 'application/octet-stream'
            else:
                type = (default or text_type(body)
                        or 'text/x-unknown-content-type')
        else:
            type = default or 'text/x-unknown-content-type'

    return type.lower(), enc and enc.lower() or None


def add_files(filenames):
    # Make sure the additional files are either loaded or scheduled to
    # be loaded:
    if mimetypes.inited:
        # Re-initialize the mimetypes module, loading additional files
        mimetypes.init(filenames)
    else:
        # Tell the mimetypes module about the additional files so
        # when it is initialized, it will pick up all of them, in
        # the right order.
        mimetypes.knownfiles.extend(filenames)


# Provide definitions shipped as part of Zope:
here = os.path.dirname(os.path.abspath(__file__))
add_files([os.path.join(here, "mime.types")])


if __name__ == '__main__':
    items = mimetypes.types_map.items()
    items.sort()
    for item in items: print "%s:\t%s" % item
