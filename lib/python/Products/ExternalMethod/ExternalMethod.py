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

"""External Method Product

This product provides support for external methods, which allow
domain-specific customization of web environments.
"""
__version__='$Revision: 1.52 $'[11:-2]
from Globals import Persistent, DTMLFile, MessageDialog, HTML
import OFS.SimpleItem, Acquisition
import AccessControl.Role, sys, os, stat, traceback
from OFS.SimpleItem import pretty_tb
from App.Extensions import getObject, getPath, FuncCode
from Globals import DevelopmentMode
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

class ExternalMethod(OFS.SimpleItem.Item, Persistent, Acquisition.Explicit,
                     AccessControl.Role.RoleManager, Navigation):
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

    func_defaults = ComputedAttribute(lambda self: self.getFuncDefaults())
    func_code = ComputedAttribute(lambda self: self.getFuncCode())


    ZopeTime=Acquisition.Acquired
    HelpSys=Acquisition.Acquired
    manage_page_header=Acquisition.Acquired

    manage_options=(
        (
        {'label':'Properties', 'action':'manage_main',
         'help':('ExternalMethod','External-Method_Properties.stx')},
        {'label':'Test', 'action':'',
         'help':('ExternalMethod','External-Method_Try-It.stx')},
        )
        +OFS.SimpleItem.Item.manage_options
        +AccessControl.Role.RoleManager.manage_options
        )

    __ac_permissions__=(
        ('View management screens', ('manage_main',)),
        ('Change External Methods', ('manage_edit',)),
        ('View', ('__call__','')),
        )

    def __init__(self, id, title, module, function):
        self.id=id
        self.manage_edit(title, module, function)

    manage_main=DTMLFile('dtml/methodEdit', globals())
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

    if DevelopmentMode:
        # In development mode we do an automatic reload
        # if the module code changed
        def getFuncDefaults(self):
            self.reloadIfChanged()
            if not hasattr(self, '_v_func_defaults'):
                self._v_f = self.getFunction()
            return self._v_func_defaults

        def getFuncCode(self):
            self.reloadIfChanged()
            if not hasattr(self, '_v_func_code'):
                self._v_f = self.getFunction()
            return self._v_func_code
    else:
        def getFuncDefaults(self):
            if not hasattr(self, '_v_func_defaults'):
                self._v_f = self.getFunction()
            return self._v_func_defaults

        def getFuncCode(self):
            if not hasattr(self, '_v_func_code'):
                self._v_f = self.getFunction()
            return self._v_func_code

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

        filePath = self.filepath()
        if filePath==None:
            raise RuntimeError,\
                "external method could not be called " \
                "because it is None"

        if not os.path.exists(filePath):
            raise RuntimeError,\
                "external method could not be called " \
                "because the file does not exist"

        if DevelopmentMode:
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
