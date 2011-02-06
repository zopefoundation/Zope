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



def manage_addExternalMethod(id, title, module, function):
    """
    Add an external method to an
    'ObjectManager'.

    In addition to the standard object-creation arguments,
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

class ExternalMethod:
    """
    Web-callable functions that encapsulate external
    Python functions.

    The function is defined in an external file.  This file is treated
    like a module, but is not a module.  It is not imported directly,
    but is rather read and evaluated.  The file must reside in the
    'Extensions' subdirectory of the Zope installation, or in an
    'Extensions' subdirectory of a product directory.

    Due to the way ExternalMethods are loaded, it is not *currently*
    possible to import Python modules that reside in the 'Extensions'
    directory.  It is possible to import modules found in the
    'lib/python' directory of the Zope installation, or in
    packages that are in the 'lib/python' directory.

    """

    __constructor__=manage_addExternalMethod

    def manage_edit(title, module, function, REQUEST=None):
        """
        Change the
        External Method.

        See the description of manage_addExternalMethod for a
        description of the arguments 'module' and 'function'.

        Note that calling 'manage_edit' causes the "module" to be
        effectively reloaded.  This is useful during debugging to see
        the effects of changes, but can lead to problems of functions
        rely on shared global data.

        """

    def __call__(*args, **kw):

        """
        Call the
        External Method.

        Calling an External Method is roughly equivalent to calling
        the original actual function from Python.  Positional and
        keyword parameters can be passed as usual.  Note however that
        unlike the case of a normal Python method, the "self" argument
        must be passed explicitly.  An exception to this rule is made
        if:

        - The supplied number of arguments is one less than the
          required number of arguments, and

        - The name of the function's first argument is 'self'.

        In this case, the URL parent of the object is supplied as the
        first argument.

        """
