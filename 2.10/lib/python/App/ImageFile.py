##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
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
import time

import Acquisition
import Globals
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from App.config import getConfiguration
from Globals import package_home
from Common import rfc1123_date
from DateTime import DateTime

from zope.contenttype import guess_content_type

class ImageFile(Acquisition.Explicit):
    """Image objects stored in external files."""

    security = ClassSecurityInfo()

    def __init__(self,path,_prefix=None):
        if _prefix is None:
            _prefix=getConfiguration().softwarehome
        elif type(_prefix) is not type(''):
            _prefix=package_home(_prefix)
        path = os.path.join(_prefix, path)
        self.path=path
        if Globals.DevelopmentMode:
            # In development mode, a shorter time is handy
            max_age = 60 # One minute
        else:
            # A longer time reduces latency in production mode
            max_age = 3600 # One hour
        self.cch = 'public,max-age=%d' % max_age

        data = open(path, 'rb').read()
        content_type, enc=guess_content_type(path, data)
        if content_type:
            self.content_type=content_type
        else:
            self.content_type='image/%s' % path[path.rfind('.')+1:]
        self.__name__=path[path.rfind('/')+1:]
        self.lmt=float(os.stat(path)[8]) or time.time()
        self.lmh=rfc1123_date(self.lmt)


    def index_html(self, REQUEST, RESPONSE):
        """Default document"""
        # HTTP If-Modified-Since header handling. This is duplicated
        # from OFS.Image.Image - it really should be consolidated
        # somewhere...
        RESPONSE.setHeader('Content-Type', self.content_type)
        RESPONSE.setHeader('Last-Modified', self.lmh)
        RESPONSE.setHeader('Cache-Control', self.cch)
        header=REQUEST.get_header('If-Modified-Since', None)
        if header is not None:
            header=header.split(';')[0]
            # Some proxies seem to send invalid date strings for this
            # header. If the date string is not valid, we ignore it
            # rather than raise an error to be generally consistent
            # with common servers such as Apache (which can usually
            # understand the screwy date string as a lucky side effect
            # of the way they parse it).
            try:    mod_since=long(DateTime(header).timeTime())
            except: mod_since=None
            if mod_since is not None:
                if getattr(self, 'lmt', None):
                    last_mod = long(self.lmt)
                else:
                    last_mod = long(0)
                if last_mod > 0 and last_mod <= mod_since:
                    RESPONSE.setStatus(304)
                    return ''

        return open(self.path,'rb').read()

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
