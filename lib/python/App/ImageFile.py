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
"""Image object that is stored in a file"""

__version__='$Revision: 1.14 $'[11:-2]

from OFS.content_types import guess_content_type
from Globals import package_home
from Common import rfc1123_date
from string import rfind, split
from DateTime import DateTime
from time import time
from os import stat
import Acquisition
import string, os


class ImageFile(Acquisition.Explicit):
    """Image objects stored in external files."""

    def __init__(self,path,_prefix=None):
        if _prefix is None: _prefix=SOFTWARE_HOME
        elif type(_prefix) is not type(''):
            _prefix=package_home(_prefix)
        path = os.path.join(_prefix, path)
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


    def index_html(self, REQUEST, RESPONSE):
        """Default document"""
        # HTTP If-Modified-Since header handling. This is duplicated
        # from OFS.Image.Image - it really should be consolidated
        # somewhere...
        header=REQUEST.get_header('If-Modified-Since', None)
        if header is not None:
            header=string.split(header, ';')[0]
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

        RESPONSE.setHeader('Content-Type', self.content_type)
        RESPONSE.setHeader('Last-Modified', self.lmh)
        f=open(self.path,'rb')
        data=f.read()
        f.close()
        return data

    HEAD__roles__=None
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

