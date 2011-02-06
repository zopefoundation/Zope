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
"""External Method Product

This product provides support for external methods, which allow
domain-specific customization of web environments.
"""
__version__='$Revision: 1.52 $'[11:-2]

import os
import stat
import sys
import traceback

from AccessControl.Permissions import change_external_methods
from AccessControl.Permissions import view_management_screens
from AccessControl.Permissions import view as View
from AccessControl.Role import RoleManager
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Acquired
from Acquisition import Explicit
from App.class_init import InitializeClass
from App.Dialogs import MessageDialog
from App.Extensions import getObject
from App.Extensions import getPath
from App.Extensions import FuncCode
from App.special_dtml import DTMLFile
from App.special_dtml import HTML
from OFS.SimpleItem import Item
from OFS.SimpleItem import pretty_tb
from Persistence import Persistent
from App.Management import Navigation
from ComputedAttribute import ComputedAttribute

manage_addExternalMethodForm=DTMLFile('dtml/methodAdd', globals())

def manage_addExternalMethod(self, id, title, module, function, REQUEST=None):
    """Add an external method to a folder

    Un addition to the standard object-creation arguments,
    'id' and title, the following arguments are defined:

        function -- The name of the python function. This can be a
          an ordinary Python function, or a bound method.

        module -- The name of the file containing the function
          definition.

        The module normally resides in the 'Extensions'
        directory, however, the file name may have a prefix of
        'product.', indicating that it should be found in a product
        directory.

        For example, if the module is: 'ACMEWidgets.foo', then an
        attempt will first be made to use the file
        'lib/python/Products/ACMEWidgets/Extensions/foo.py'. If this
        failes, then the file 'Extensions/ACMEWidgets.foo.py' will be
        used.
    """
    id=str(id)
    title=str(title)
    module=str(module)
    function=str(function)

    i=ExternalMethod(id,title,module,function)
    self._setObject(id,i)
    if REQUEST is not None:
        return self.manage_main(self,REQUEST)

class ExternalMethod(Item, Persistent, Explicit,
                     RoleManager, Navigation):
    """Web-callable functions that encapsulate external python functions.

    The function is defined in an external file.  This file is treated
    like a module, but is not a module.  It is not imported directly,
    but is rather read and evaluated.  The file must reside in the
    'Extensions' subdirectory of the Zope installation, or in an
    'Extensions' subdirectory of a product directory.

    Due to the way ExternalMethods are loaded, it is not *currently*
    possible to use Python modules that reside in the 'Extensions'
    directory.  It is possible to load modules found in the
    'lib/python' directory of the Zope installation, or in
    packages that are in the 'lib/python' directory.

    """

    meta_type = 'External Method'

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    func_defaults = ComputedAttribute(lambda self: self.getFuncDefaults())
    func_code = ComputedAttribute(lambda self: self.getFuncCode())


    ZopeTime = Acquired
    HelpSys = Acquired
    manage_page_header = Acquired

    manage_options=(
        (
        {'label':'Properties', 'action':'manage_main',
         'help':('ExternalMethod','External-Method_Properties.stx')},
        {'label':'Test', 'action':'',
         'help':('ExternalMethod','External-Method_Try-It.stx')},
        )
        + Item.manage_options
        + RoleManager.manage_options
        )

    def __init__(self, id, title, module, function):
        self.id=id
        self.manage_edit(title, module, function)

    security.declareProtected(view_management_screens, 'manage_main')
    manage_main=DTMLFile('dtml/methodEdit', globals())

    security.declareProtected(change_external_methods, 'manage_edit')
    def manage_edit(self, title, module, function, REQUEST=None):
        """Change the external method

        See the description of manage_addExternalMethod for a
        descriotion of the arguments 'module' and 'function'.

        Note that calling 'manage_edit' causes the "module" to be
        effectively reloaded.  This is useful during debugging to see
        the effects of changes, but can lead to problems of functions
        rely on shared global data.
        """
        title=str(title)
        module=str(module)
        function=str(function)

        self.title=title
        if module[-3:]=='.py': module=module[:-3]
        elif module[-4:]=='.pyc': module=module[:-4]
        self._module=module
        self._function=function
        self.getFunction(1)
        if REQUEST:
            message="External Method Uploaded."
            return self.manage_main(self,REQUEST,manage_tabs_message=message)

    def getFunction(self, reload=0):

        f=getObject(self._module, self._function, reload)
        if hasattr(f,'im_func'): ff=f.im_func
        else: ff=f

        self._v_func_defaults  = ff.func_defaults
        self._v_func_code = FuncCode(ff,f is not ff)

        self._v_f=f

        return f

    def reloadIfChanged(self):
        # If the file has been modified since last loaded, force a reload.
        ts=os.stat(self.filepath())[stat.ST_MTIME]
        if (not hasattr(self, '_v_last_read') or
            (ts != self._v_last_read)):
            self._v_f=self.getFunction(1)
            self._v_last_read=ts

    def getFuncDefaults(self):
        import Globals  # for data
        if Globals.DevelopmentMode:
            self.reloadIfChanged()
        if not hasattr(self, '_v_func_defaults'):
            self._v_f = self.getFunction()
        return self._v_func_defaults

    def getFuncCode(self):
        import Globals  # for data
        if Globals.DevelopmentMode:
            self.reloadIfChanged()
        if not hasattr(self, '_v_func_code'):
            self._v_f = self.getFunction()
        return self._v_func_code

    security.declareProtected(View, '__call__')
    def __call__(self, *args, **kw):
        """Call an ExternalMethod

        Calling an External Method is roughly equivalent to calling
        the original actual function from Python.  Positional and
        keyword parameters can be passed as usual.  Note however that
        unlike the case of a normal Python method, the "self" argument
        must be passed explicitly.  An exception to this rule is made
        if:

        - The supplied number of arguments is one less than the
          required number of arguments, and

        - The name of the function\'s first argument is 'self'.

        In this case, the URL parent of the object is supplied as the
        first argument.
        """
        import Globals  # for data

        filePath = self.filepath()
        if filePath==None:
            raise RuntimeError,\
                "external method could not be called " \
                "because it is None"

        if not os.path.exists(filePath):
            raise RuntimeError,\
                "external method could not be called " \
                "because the file does not exist"

        if Globals.DevelopmentMode:
            self.reloadIfChanged()

        if hasattr(self, '_v_f'):
            f=self._v_f
        else:
            f=self.getFunction()

        __traceback_info__=args, kw, self._v_func_defaults

        try: return f(*args, **kw)
        except TypeError, v:
            tb=sys.exc_info()[2]
            try:
                if ((self._v_func_code.co_argcount-
                     len(self._v_func_defaults or ()) - 1 == len(args))
                    and self._v_func_code.co_varnames[0]=='self'):
                    return f(self.aq_parent.this(), *args, **kw)

                raise TypeError, v, tb
            finally: tb=None


    def function(self): return self._function
    def module(self): return self._module

    def filepath(self):
        if not hasattr(self, '_v_filepath'):
            self._v_filepath=getPath('Extensions', self._module,
                                     suffixes=('','py','pyc','pyp'))
        return self._v_filepath

InitializeClass(ExternalMethod)
