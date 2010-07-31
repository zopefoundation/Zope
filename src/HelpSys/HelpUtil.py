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
"""Help system support module"""

import re
import sys

from AccessControl.class_init import InitializeClass
from Acquisition import Implicit
from App.Dialogs import MessageDialog
from App.special_dtml import HTML
from Persistence import Persistent
from zope.structuredtext.html import HTMLWithImages 
from zope.structuredtext.document import DocumentWithImages


class HelpBase(Implicit):
    """ """
    def __bobo_traverse__(self, REQUEST, name=None):
        # A sneaky trick - we cant really _have_ an index_html
        # because that would often hide the index_html of a
        # wrapped object ;(
        if name=='index_html':
            return self.hs_index
        return getattr(self, name)

    def __len__(self):
        return 1


class object(Implicit):
    def __init__(self, name, ob, op=None):
        self._name=name
        self._obj_=ob
        self._obp_=op

    def __getattr__(self, name):
        return getattr(self.__dict__['_obj_'], name)

    def __len__(self):
        return 1

    def get_id(self):
        return id(self._obj_)

    def get_name(self):
        return self._name

    def get_type(self):
        return type(self._obj_).__name__

    def get_value(self):
        return self._obj_

    def get_docstring(self):
        if hasattr(self._obj_, '__doc__'):
            doc=self._obj_.__doc__
            if not doc: doc=''
            return doc
        return ''

    def get_docstring_html(self):
        doc=self.get_docstring()
        if doc.find('\n\n') > -1:
            doc=doc.split('\n\n')
            if len(doc) > 1:
                doc[1]=doc[1].strip()
            doc='\n\n'.join(doc)


        doc = DocumentWithImages()(doc)
        return HTMLWithImages()(doc)


    def version(self):
        return None

    tpId   =get_name
    tpURL  =get_name
    __str__=get_name


class moduleobject(object):
    def get_file(self):
        if hasattr(self._obj_, '__file__'):
            return self._obj_.__file__

    def get_modules(self):
        data=[]
        for name, ob in self._obj_.__dict__.items():
            if is_module(ob) and _chModule(name, ob):
                data.append(moduleobject(name, ob, self))
        return data

    def get_classes(self):
        data=[]
        for name, ob in self._obj_.__dict__.items():
            if is_class(ob) and _chClass(name, ob):
                data.append(classobject(name, ob, self))
        return data


class classobject(object):
    def get_metatype(self):
        try: return self._obj_.meta_type
        except:
            t, v = sys.exc_info()[:2]
            return '%s %s' % (t, v)

    def get_module(self):
        if hasattr(self._obj_, '__module__'):
            module=sys.modules[self._obj_.__module__]
            return moduleobject(module.__name__, module)

    def get_file(self):
        return self.get_module().get_file()

    def get_bases(self):
        bases=[]
        if hasattr(self._obj_, '__bases__'):
            for base in self._obj_.__bases__:
                bases.append(classobject(base.__name__, base))
        return bases

    def get_base_list(self, list=None):
        if list is None: list=[]
        list.append(self)
        for base in self.get_bases():
            list=base.get_base_list(list)
        return list

    def get_methods(self):
        keys=self._obj_.__dict__.keys()
        dict=self._obj_.__dict__
        keys.sort()
        methods=[]
        for name in keys:
            ob=dict[name]
            if is_method(ob) and _chMethod(name, ob):
                methods.append(methodobject(name, ob, self))
        return methods

    def get_method_dict(self, dict=None):
        if dict is None:
            dict={}
        dup=dict.has_key
        for method in self.get_methods():
            name=method.get_name()
            if not dup(name):
                dict[name]=method
        for base in self.get_bases():
            dict=base.get_method_dict(dict)
        return dict

    def get_method_list(self):
        dict=self.get_method_dict()
        keys=dict.keys()
        keys.sort()
        list=[]
        for key in keys:
            list.append(dict[key])
        del dict
        return list

##     def obAttributes(self):
##         # Return list of class attributes
##         keys=self._obj_.__dict__.keys()
##         dict=self._obj_.__dict__
##         keys.sort()
##         attrs=[]
##         for name in keys:
##             ob=dict[name]
##             if _isAttribute(ob) and _chAttribute(name, ob):
##                 attrs.append(AttributeObject(name, ob, self))
##         return attrs

##     def obAttributeDict(self, dict=None):
##         # Return dict of attrs in class and superclasses
##         if dict is None:
##             dict={}
##             root=1
##         else: root=0
##         dup=dict.has_key
##         for attr in self._obj_Attributes():
##             name=attr.obName()
##             if not dup(name):
##                 dict[name]=attr
##         for base in self._obj_Bases():
##             dict=base.obAttributeDict(dict)
##         return dict

##     def obAttributeList(self):
##         # Return list of attrs in class and superclasses
##         dict=self._obj_AttributeDict()
##         keys=dict.keys()
##         keys.sort()
##         list=[]
##         append=list.append
##         for name in keys:
##             append(dict[name])
##             del dict
##         return list



# needs to be tested !!! The conversion of reconvert.convert looks suspicious
sig_match=re.compile(r'[\w]*\([^)]*\)').match # matches "f(arg1, arg2)"
pre_match=re.compile(r'[\w]*\([^)]*\)[ -]*').match # with ' ' or '-' included

class methodobject(object):

    def get_class(self):
        return self._obp_

    def get_module(self):
        return self.get_class().get_module()

    def get_file(self):
        return self.get_module().get_file()

    def get_docstring(self):
        func=self._obj_
        doc=''
        if hasattr(func, 'im_func'):
            func=func.im_func
        if hasattr(func, '__doc__'):
            doc=func.__doc__
            if not doc: doc=''
            doc=doc.strip()
        if hasattr(func, 'func_code'):
            if hasattr(func.func_code, 'co_varnames'):
                return doc
        mo=pre_match(doc)
        if mo is not None:
            return doc[mo.end(0):]
        return doc

    def get_signaturex(self):
        name=self._name
        func=self._obj_
        method=None

        if hasattr(func, 'im_func'):
            method=1
            func=func.im_func

        # Normal functions
        if hasattr(func, 'func_code'):
            if hasattr(func.func_code, 'co_varnames'):
                args=map(lambda x: x,
                     func.func_code.co_varnames[:func.func_code.co_argcount])
                ndefaults=func.func_defaults
                ndefaults=ndefaults and len(ndefaults) or 0
                if '__ick__' in args:
                    nick=len(args)-args.index('__ick__')
                    args=args[:-nick]
                    ndefaults=ndefaults-nick
                if ndefaults > 0:
                    args[-ndefaults]='['+args[-ndefaults]
                    args[-1]=args[-1]+']'
                if method: args=args[1:]
                if name=='__call__':
                    name='Call Operation'
                return '%s(%s)' % (name, ', '.join(args))

        # Other functions - look for something that smells like
        # a signature at the beginning of the docstring.
        if hasattr(func, '__doc__'):
            doc=func.__doc__
            if not doc: doc=''
            doc=doc.strip()
            mo=sig_match(doc)
            if mo is not None:
                return doc[:mo.end(0)]
        return '%s()' % name


    def get_signature(self):
        try: return self.get_signaturex()
        except:
            t, v = sys.exc_info()[:2]
            return '%s %s' % (t, v)


## class AttributeObject(_ob_):
##     def obClass(self):
##         return self.op

##     def obModule(self):
##         return self.obClass().obModule()

##     def obFile(self):
##         return self.obModule().obFile()

## class InstanceObject(_ob_):
##     def obClass(self):
##         # Return the class for this instance
##         c=self._obj_.__class__
##         return ClassObject(c.__name__, c)

##     def obClassList(self):
##         # Return list of all superclasses
##         return self._obj_Class().obClassList()

##     def obMethods(self):
##         # Return list of instance methods
##         keys=self._obj_.__dict__.keys()
##         dict=self._obj_.__dict__
##         keys.sort()
##         methods=[]
##         for name in keys:
##             ob=dict[name]
##             if _isMethod(ob) and _chMethod(name, ob):
##                methods.append(MethodObject(name, ob))
##         return methods

##     def obMethodDict(self):
##         # Return dict of instance and superclass methods
##         dict=self._obj_Class().obMethodDict()
##         for method in self._obj_Methods():
##             dict[method.obName()]=method
##         return dict

##     def obMethodList(self):
##         # Return list of instance and superclass methods
##         dict=self._obj_MethodDict()
##         keys=dict.keys()
##         keys.sort()
##         list=[]
##         append=list.append
##         for name in keys:
##             append(dict[name])
##         return list

##     def obAttributes(self):
##         # Return list of instance attributes
##         keys=self._obj_.__dict__.keys()
##         dict=self._obj_.__dict__
##         keys.sort()
##         attrs=[]
##         for name in keys:
##             ob=dict[name]
##             if _isAttribute(ob) and _chAttribute(name, ob):
##                 attrs.append(AttributeObject(name, ob, self))
##         return attrs

##     def obAttributeDict(self):
##         # Return dict of instance and superclass attributes
##         dict=self._obj_Class().obAttributeDict()
##         for attr in self._obj_Attributes():
##             dict[attr.obName()]=attr
##         return dict

##     def obAttributeList(self):
##         # Return list of instance and superclass attributes
##         dict=self._obj_AttributeDict()
##         keys=dict.keys()
##         keys.sort()
##         list=[]
##         append=list.append
##         for name in keys:
##             append(dict[name])
##         return list




_classtypes=(type(HTML),
             type(Persistent),
            )

_methodtypes=(type([].sort),
              type(default__class_init__),
              type(HTML.manage_edit),
              type(HTML.__changed__),
              type(MessageDialog.manage_edit),
             )

def is_module(ob):
    return type(ob)==type(sys)

def is_class(ob):
    return type(ob) in _classtypes

def is_method(ob):
    if type(ob) in _methodtypes or hasattr(ob, 'func_code'):
        return 1
    return 0

def is_attribute(ob):
    return not is_method(ob)



def _chModule(name, ob):
    if name[0]=='_':
        return 0
    return 1

def _chClass(name, ob):
    if name[0]=='_':
        return 0
    return 1

def _chMethod(name, ob):
    if name[0]=='_':
        return 0
    return 1

def _chAttribute(name, ob):
    if name[0]=='_':
        return 0
    return 1
