##############################################################################
#
# Copyright (c) 2020 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""This module offers helpers to handle HTTP headers."""

import urllib


def make_content_disposition(disposition, file_name):
    """Create HTTP header for downloading a file with a UTF-8 filename.

    See this and related answers: https://stackoverflow.com/a/8996249/2173868.
    """
    header = f'{disposition}'
    try:
        file_name.encode("latin-1")
    except UnicodeEncodeError:
        # the file cannot be encoded using the `latin-1` encoding
        # which is required for HTTP headers
        #
        # a special header has to be crafted
        # also see https://tools.ietf.org/html/rfc6266#appendix-D
        quoted_file_name = urllib.parse.quote(file_name)
        header += f'; filename*=UTF-8\'\'{quoted_file_name}'
        return header
    else:
        header += f'; filename="{file_name}"'
        return header
