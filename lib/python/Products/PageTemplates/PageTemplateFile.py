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

# XXX: this needs some more work..this class is *not* used by the
# ZopePageTemplate implementation but most likely only for class
# using PTs for edit/add forms etc. Also the tests don't pass

class PageTemplateFile(ZopePageTemplate):

    def __init__(self, filename, _prefix=None, **kw):
        self.ZBindings_edit(self._default_bindings)
        if _prefix is None:
            _prefix = getConfiguration().softwarehome
        elif not isinstance(_prefix, str):
            _prefix = package_home(_prefix)
        name = kw.get('__name__')
        basepath, ext = os.path.splitext(filename)
        if name:
            self._need__name__ = 0
            self.__name__ = name
        else:
            self.__name__ = os.path.basename(basepath)
        if not ext:
            # XXX This is pretty bogus, but can't be removed since
            # it's been released this way.
            filename = filename + '.zpt'
        self.filename = os.path.join(_prefix, filename)

        ZopePageTemplate.__init__(self, os.path.basename(self.filename), open(self.filename).read(), 'text/html')
        

InitializeClass(PageTemplateFile)
