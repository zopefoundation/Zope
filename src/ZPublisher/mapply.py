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
"""Provide an apply-like facility that works with any mapping object
"""
import zope.publisher.publish

def default_call_object(object, args, context):
    result=object(*args) # Type s<cr> to step into published object.
    return result

def default_missing_name(name, context):
    raise TypeError, 'argument %s was ommitted' % name

def default_handle_class(klass, context):
    if hasattr(klass,'__init__'):
        f=klass.__init__.im_func
        c=f.func_code
        names=c.co_varnames[1:c.co_argcount]
        return klass, names, f.func_defaults
    else:
        return klass, (), ()

def mapply(object, positional=(), keyword={},
           debug=None, maybe=None,
           missing_name=default_missing_name,
           handle_class=default_handle_class,
           context=None, bind=0,
           ):

    if hasattr(object,'__bases__'):
        f, names, defaults = handle_class(object, context)
    else:
        try:
            f, count = zope.publisher.publish.unwrapMethod(object)
        except TypeError:
            if maybe:
                return object
            raise
        code = f.func_code
        defaults = f.func_defaults
        names = code.co_varnames[count:code.co_argcount]

    nargs=len(names)
    if positional:
        positional=list(positional)
        if bind and nargs and names[0]=='self':
            positional.insert(0, missing_name('self', context))
        if len(positional) > nargs: raise TypeError, 'too many arguments'
        args=positional
    else:
        if bind and nargs and names[0]=='self':
            args=[missing_name('self', context)]
        else:
            args=[]

    get=keyword.get
    nrequired=len(names) - (len(defaults or ()))
    for index in range(len(args), len(names)):
        name=names[index]
        v=get(name, args)
        if v is args:
            if index < nrequired: v=missing_name(name, context)
            else: v=defaults[index-nrequired]
        args.append(v)

    args=tuple(args)
    if debug is not None: return debug(object,args,context)
    else: return object(*args)
