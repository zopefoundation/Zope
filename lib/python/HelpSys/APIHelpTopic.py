##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""
API documentation help topics
"""

import types
import string
import HelpTopic
from Globals import DTMLFile, Persistent

_ignore_objects = {}

try:
    import Interface
    _ignore_objects.update(Interface.__dict__)
except ImportError:
    pass

class APIHelpTopic(HelpTopic.HelpTopic):
    """
    Provides API documentation.
    """

    isAPIHelpTopic=1
    
    def __init__(self, id, title, file):
        self.id=id
        self.title=title
        dict={}
        execfile(file, dict)
        self.doc=dict.get('__doc__','')

        self.apis=[]
        for k, v in dict.items():
            if (not _ignore_objects.has_key(k) or
                _ignore_objects[k] is not v):
                if type(v)==types.ClassType:
                    # A class.
                    self.apis.append(APIDoc(v, 0))
                elif (hasattr(v, 'isImplementedByInstancesOf')):
                    # A scarecrow interface.
                    self.apis.append(APIDoc(v, 1))

        # try to get title from first non-blank line
        # of module docstring
        if not self.title:
            lines=string.split(self.doc,'\n')
            while 1:
                line=string.strip(lines[0])
                if line:
                    self.title=line
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
        for api in self.apis:
            text="%s %s" % (text, api.SearchableText())
        return text

      
class APIDoc(Persistent):
    """
    Describes an API.
    """

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
##        for base in klass.getBases():
##            names = string.split(base.__name__, '.')
##            url="%s/Help/%s.py#%s" % (names[0], names[1], names[2])
##            self.extends.append((names[2], url))

        # constructor information
##        if hasattr(klass, '__constructor__'):
##            self.constructor=MethodDoc(klass.__constructor__)
        
        # Get info on methods and attributes, ignore special items
        self.attributes=[]
        self.methods=[]
        from Interface.Method import Method
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
        #
        # The base APIs are deduced from the __extends__
        # attribute.
        
        self.name=klass.__name__ 
        self.doc=trim_doc_string(klass.__doc__)

        # inheritence information
        if hasattr(klass,'__extends__'):
            self.extends=[]
            for base in klass.__extends__:
                names=string.split(base, '.')
                url="%s/Help/%s.py#%s" % (names[0], names[1], names[2])
                self.extends.append((names[2], url))

        # constructor information
        if hasattr(klass, '__constructor__'):
            self.constructor=MethodDoc(klass.__constructor__)
        
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
    
    
class AttributeDoc(Persistent):
    """
    Describes an attribute of an API.
    """
    
    def __init__(self, name, value):
        self.name=name
        self.value=value

    view=DTMLFile('dtml/attributeView', globals())


class MethodDoc(Persistent):
    """
    Describes a method of an API.
    
    required - a sequence of required arguments 
    optional - a sequence of tuples (name, default value)
    varargs - the name of the variable argument or None
    kwargs - the name of the kw argument or None
    """
    
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


def trim_doc_string(text):
    """
    Trims a doc string to make it format
    correctly with structured text.
    """
    text=string.strip(text)
    text=string.replace(text, '\r\n', '\n')
    lines=string.split(text, '\n')
    nlines=[lines[0]]
    if len(lines) > 1:
        min_indent=None
        for line in lines[1:]:
            indent=len(line) - len(string.lstrip(line))
            if indent < min_indent or min_indent is None:
                min_indent=indent   
        for line in lines[1:]:
            nlines.append(line[min_indent:])
    return string.join(nlines, '\n')
    
    
    
