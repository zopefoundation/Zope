##############################################################################
#
# Copyright (c) 1996-1998, Digital Creations, Fredericksburg, VA, USA.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#   o Redistributions of source code must retain the above copyright
#     notice, this list of conditions, and the disclaimer that follows.
# 
#   o Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions, and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
# 
#   o All advertising materials mentioning features or use of this
#     software must display the following acknowledgement:
# 
#       This product includes software developed by Digital Creations
#       and its contributors.
# 
#   o Neither the name of Digital Creations nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# 
# THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS AND CONTRIBUTORS *AS IS*
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL
# CREATIONS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
#
# 
# If you have questions regarding this software, contact:
#
#   Digital Creations, L.C.
#   910 Princess Ann Street
#   Fredericksburge, Virginia  22401
#
#   info@digicool.com
#
#   (540) 371-6909
#
##############################################################################
__version__='$Revision: 1.1 $'[11:-2]

import regex
from string import atoi, atol, atof, join, split, strip

def field2string(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    return v

def field2text(v, nl=regex.compile('\r\n\|\n\r').search):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    l=nl(v)
    if l < 0: return v
    r=[]
    s=0
    while l >= s:
        r.append(v[s:l])
        s=l+2
        l=nl(v,s)
    r.append(v[s:])
        
    return join(r,'\n')

def field2required(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    if strip(v): return v
    raise ValueError, 'No input for required field<p>'

def field2int(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    # we can remove the check for an empty string when we go to python 1.4
    if v: return atoi(v)
    raise ValueError, 'Empty entry when <strong>integer</strong> expected'

def field2float(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    # we can remove the check for an empty string when we go to python 1.4
    if v: return atof(v)
    raise ValueError, (
        'Empty entry when <strong>floating-point number</strong> expected')

def field2long(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    # we can remove the check for an empty string when we go to python 1.4
    if v: return atol(v)
    raise ValueError, 'Empty entry when <strong>integer</strong> expected'

def field2tokens(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    return split(v)

def field2lines(v):
    return split(field2text(v),'\n')

def field2date(v):
    from DateTime import DateTime
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    return DateTime(v)

ListType=type([])

def field2list(v):
    if type(v) is not ListType: v=[v]
    return v

def field2tuple(v):
    if type(v) is not ListType: v=(v,)
    return tuple(v)

type_converters = {
    'float':    field2float,
    'int':      field2int,
    'long':     field2long,
    'string':   field2string,
    'date':     field2date,
    'list':     field2list,
    'tuple':    field2tuple,
    'required': field2required,
    'tokens':   field2tokens,
    'lines':    field2lines,
    'text':     field2text,
    }

