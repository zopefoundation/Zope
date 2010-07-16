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
"""Image object that is stored in a file"""

__version__='$Revision: 1.20 $'[11:-2]

import os
import os.path
import stat
import time
import warnings

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Explicit
from App.class_init import InitializeClass
from App.Common import package_home
from App.Common import rfc1123_date
from App.config import getConfiguration
from DateTime.DateTime import DateTime
from zope.contenttype import guess_content_type
from ZPublisher.Iterators import filestream_iterator

import Zope2
PREFIX = os.path.realpath(
    os.path.join(os.path.dirname(Zope2.__file__), os.path.pardir))

NON_PREFIX_WARNING = ('Assuming image location to be present in the Zope2 '
                      'distribution. This is deprecated and might lead to '
                      'broken code if the directory in question is moved '
                      'to another distribution. Please provide either an '
                      'absolute file system path or a prefix. Support for '
                      'relative filenames without a prefix might be '
                      'dropped in a future Zope2 release.')


class ImageFile(Explicit):
    """Image objects stored in external files."""

    security = ClassSecurityInfo()

    def __init__(self, path, _prefix=None):
        import Globals  # for data
        if _prefix is None:
            _prefix=getattr(getConfiguration(), 'softwarehome', None) or PREFIX
            if not os.path.isabs(path):
                warnings.warn(NON_PREFIX_WARNING, UserWarning, 2)
        elif type(_prefix) is not type(''):
            _prefix=package_home(_prefix)
        # _prefix is ignored if path is absolute
        path = os.path.join(_prefix, path)
        self.path=path
        if Globals.DevelopmentMode:
            # In development mode, a shorter time is handy
            max_age = 60 # One minute
        else:
            # A longer time reduces latency in production mode
            max_age = 3600 # One hour
        self.cch = 'public,max-age=%d' % max_age

        # First try to get the content_type by name
        content_type, enc=guess_content_type(path, default='failed')

        if content_type == 'failed':
            # This failed, lets look into the file content
            img = open(path, 'rb')
            data = img.read(1024) # 1k should be enough
            img.close()

            content_type, enc=guess_content_type(path, data)

        if content_type:
            self.content_type=content_type
        else:
            ext = os.path.splitext(path)[-1].replace('.', '')
            self.content_type = 'image/%s' % ext

        self.__name__ = os.path.split(path)[-1]
        stat_info = os.stat(path)
        self.size = stat_info[stat.ST_SIZE]
        self.lmt = float(stat_info[stat.ST_MTIME]) or time.time()
        self.lmh = rfc1123_date(self.lmt)

    def index_html(self, REQUEST, RESPONSE):
        """Default document"""
        # HTTP If-Modified-Since header handling. This is duplicated
        # from OFS.Image.Image - it really should be consolidated
        # somewhere...
        RESPONSE.setHeader('Content-Type', self.content_type)
        RESPONSE.setHeader('Last-Modified', self.lmh)
        RESPONSE.setHeader('Cache-Control', self.cch)
        RESPONSE.setHeader('Content-Length', str(self.size).replace('L', ''))
        header = REQUEST.get_header('If-Modified-Since', None)
        if header is not None:
            header=header.split(';')[0]
            # Some proxies seem to send invalid date strings for this
            # header. If the date string is not valid, we ignore it
            # rather than raise an error to be generally consistent
            # with common servers such as Apache (which can usually
            # understand the screwy date string as a lucky side effect
            # of the way they parse it).
            try:
                mod_since = long(DateTime(header).timeTime())
            except:
                mod_since = None
            if mod_since is not None:
                if getattr(self, 'lmt', None):
                    last_mod = long(self.lmt)
                else:
                    last_mod = long(0)
                if last_mod > 0 and last_mod <= mod_since:
                    RESPONSE.setStatus(304)
                    return ''

        return filestream_iterator(self.path, mode='rb')

    security.declarePublic('HEAD')
    def HEAD(self, REQUEST, RESPONSE):
        """ """
        RESPONSE.setHeader('Content-Type', self.content_type)
        RESPONSE.setHeader('Last-Modified', self.lmh)
        return ''

    def __len__(self):
        # This is bogus and needed because of the way Python tests truth.
        return 1

    def __str__(self):
        return '<img src="%s" alt="" />' % self.__name__

InitializeClass(ImageFile)
