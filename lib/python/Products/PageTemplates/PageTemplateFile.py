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

import os

from Globals import package_home, InitializeClass
from App.config import getConfiguration
from ZopePageTemplate import ZopePageTemplate
from zope.app.content_types import guess_content_type

from OFS.SimpleItem import SimpleItem
from zope.pagetemplate.pagetemplatefile import PageTemplateFile as PTF


class PageTemplateFile(SimpleItem, PTF):

    def __init__(self, filename, _prefix=None, **kw):
        name = None
        if kw.has_key('__name__'):
            name = kw['__name__']
            del kw['__name__'] 

        PTF.__init__(self, filename, _prefix, **kw)

        basepath, ext = os.path.splitext(filename)
        if name:
            self.id = self.__name__ = name
        else:
            self.id = self.__name__ = os.path.basename(basepath)

InitializeClass(PageTemplateFile)
