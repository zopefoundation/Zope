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
""" API documentation help topics.
"""

import types

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.special_dtml import DTMLFile
from Persistence import Persistent

from HelpTopic import HelpTopic # XXX relative to avoid cycle

_ignore_objects = {}

class APIHelpTopic(HelpTopic):
    """ Provides API documentation.
    """

    isAPIHelpTopic=1
    funcs=() # for backward compatibility

    def __init__(self, id, title, file):
        self.id=id
        self.title=title
        dict={}
        execfile(file, dict)
        self.doc=dict.get('__doc__','')

        self.apis=[]
        self.funcs=[]
        for k, v in dict.items():
            if (not _ignore_objects.has_key(k) or
                _ignore_objects[k] is not v):
                if type(v)==types.ClassType:
                    # A class.
                    self.apis.append(APIDoc(v, 0))
                elif (hasattr(v, 'implementedBy')):
                    # A zope.interface.Interface.
                    self.apis.append(APIDoc(v, 1))
                elif type(v)==types.FunctionType:
                    # A function
                    self.funcs.append(MethodDoc(v, 0))
        # try to get title from first non-blank line
        # of module docstring
        if not self.title:
            lines=self.doc.split('\n')
            while 1:
                line=lines[0].strip()
                if line:
                    # get rid of anything after a colon in the line
                    self.title=line.split(':')[0]
                    break
                lines.pop(0)
                if not lines:
                    break
        # otherwise get title from first class name
        if not self.title:
            self.title=self.apis[0].name

    index_html=DTMLFile('dtml/APIHelpView', globals())

    def SearchableText(self):
        "The full text of the Help Topic, for indexing purposes"
        text="%s %s" % (self.title, self.doc)
        for api in self.apis + self.funcs:
            try:  # not all api's provide SearchableText()
                text="%s %s" % (text, api.SearchableText())
            except AttributeError: pass
        return text


class APIDoc(Persistent):
    """ Describes an API.
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess( {'attributes': True, 'constructor': True,
                                'doc': True, 'extends': True, 'name': True,
                                'methods': True} )

    extends=()

    def __init__(self, klass, isInterface=0):
        if isInterface:
            self._createFromInterface(klass)
        else:
            self._createFromClass(klass)

    def _createFromInterface(self, klass):
        # Creates an APIDoc instance given an interface object.
        self.name=klass.__name__
        self.doc=trim_doc_string(klass.__doc__)

        # inheritence information
        self.extends=[]

        # Get info on methods and attributes, ignore special items
        self.attributes=[]
        self.methods=[]
        for k,v in klass.namesAndDescriptions():
            if hasattr(v, 'getSignatureInfo'):
                self.methods.append(MethodDoc(v, 1))
            else:
                self.attributes.append(AttributeDoc(k, v.__doc__))

    def _createFromClass(self, klass):
        # Creates an APIDoc instance given a python class.
        # the class describes the API; it contains
        # methods, arguments and doc strings.
        #
        # The name of the API is deduced from the name
        # of the class.

        self.name=klass.__name__
        self.doc=trim_doc_string(klass.__doc__)

        # Get info on methods and attributes, ignore special items
        self.attributes=[]
        self.methods=[]
        for k,v in klass.__dict__.items():
            if k not in ('__extends__', '__doc__', '__constructor__'):
                if type(v)==types.FunctionType:
                    self.methods.append(MethodDoc(v, 0))
                else:
                    self.attributes.append(AttributeDoc(k, v))

    def SearchableText(self):
        """
        The full text of the API, for indexing purposes.
        """
        text="%s %s" % (self.name, self.doc)
        for attribute in self.attributes:
            text="%s %s" % (text, attribute.name)
        for method in self.methods:
            text="%s %s %s" % (text, method.name, method.doc)
        return text

    view=DTMLFile('dtml/APIView', globals())

InitializeClass(APIDoc)


class AttributeDoc(Persistent):
    """ Describes an attribute of an API.
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess( {'name': True, 'value': True} )

    def __init__(self, name, value):
        self.name=name
        self.value=value

    view=DTMLFile('dtml/attributeView', globals())

InitializeClass(AttributeDoc)


class MethodDoc(Persistent):
    """ Describes a method of an API.

    required - a sequence of required arguments
    optional - a sequence of tuples (name, default value)
    varargs - the name of the variable argument or None
    kwargs - the name of the kw argument or None
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess( {'doc': True, 'kwargs': True, 'name': True,
                                'optional': True, 'required': True,
                                'varargs': True} )

    varargs=None
    kwargs=None

    def __init__(self, func, isInterface=0):
        if isInterface:
            self._createFromInterfaceMethod(func)
        else:
            self._createFromFunc(func)

    def _createFromInterfaceMethod(self, func):
        self.name = func.__name__
        self.doc = trim_doc_string(func.__doc__)
        self.required = func.required
        opt = []
        for p in func.positional[len(func.required):]:
            opt.append((p, func.optional[p]))
        self.optional = tuple(opt)
        if func.varargs:
            self.varargs = func.varargs
        if func.kwargs:
            self.kwargs = func.kwargs

    def _createFromFunc(self, func):
        if hasattr(func, 'im_func'):
            func=func.im_func

        self.name=func.__name__
        self.doc=trim_doc_string(func.__doc__)

        # figure out the method arguments
        # mostly stolen from pythondoc
        CO_VARARGS = 4
        CO_VARKEYWORDS = 8
        names = func.func_code.co_varnames
        nrargs = func.func_code.co_argcount
        if func.func_defaults:
            nrdefaults = len(func.func_defaults)
        else:
            nrdefaults = 0
        self.required = names[:nrargs-nrdefaults]
        if func.func_defaults:
            self.optional = tuple(map(None, names[nrargs-nrdefaults:nrargs],
                                 func.func_defaults))
        else:
            self.optional = ()
        varargs = []
        ix = nrargs
        if func.func_code.co_flags & CO_VARARGS:
            self.varargs=names[ix]
            ix = ix+1
        if func.func_code.co_flags & CO_VARKEYWORDS:
            self.kwargs=names[ix]

    view=DTMLFile('dtml/methodView', globals())

InitializeClass(MethodDoc)


def trim_doc_string(text):
    """
    Trims a doc string to make it format
    correctly with structured text.
    """
    text=text.strip()
    text=text.replace( '\r\n', '\n')
    lines=text.split('\n')
    nlines=[lines[0]]
    if len(lines) > 1:
        min_indent=None
        for line in lines[1:]:
            if not line:
                continue
            indent=len(line) - len(line.lstrip())
            if indent < min_indent or min_indent is None:
                min_indent=indent
        for line in lines[1:]:
            nlines.append(line[min_indent:])
    return '\n'.join(nlines)
