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
"""Provide an apply-like facility that works with any mapping object
"""

def default_call_object(object, args, context):
    result=apply(object,args) # Type s<cr> to step into published object.
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
        f=object
        im=0
        if hasattr(f, 'im_func'):
            im=1
        elif not hasattr(f,'func_defaults'):
            if hasattr(f, '__call__'):
                f=f.__call__
                if hasattr(f, 'im_func'):
                    im=1
                elif not hasattr(f,'func_defaults') and maybe: return object
            elif maybe: return object
    
        if im:
            f=f.im_func
            c=f.func_code
            defaults=f.func_defaults
            names=c.co_varnames[1:c.co_argcount]
        else:
            defaults=f.func_defaults
            c=f.func_code
            names=c.co_varnames[:c.co_argcount]

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
    else: return apply(object,args)
