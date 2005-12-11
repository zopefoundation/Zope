
import os

from Globals import package_home, InitializeClass
from ZopePageTemplate import ZopePageTemplate

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
