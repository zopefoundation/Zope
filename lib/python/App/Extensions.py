##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################
__doc__='''Standard routines for handling Principia Extensions

Principia extensions currently include external methods and pluggable brains.

$Id: Extensions.py,v 1.4 1998/12/04 20:15:25 jim Exp $'''
__version__='$Revision: 1.4 $'[11:-2]

from string import find
import os, zlib, rotor
path_split=os.path.split
exists=os.path.exists
    
class FuncCode:

    def __init__(self, f, im=0):
        self.co_varnames=f.func_code.co_varnames[im:]
        self.co_argcount=f.func_code.co_argcount-im

    def __cmp__(self,other):
        return cmp((self.co_argcount, self.co_varnames),
                   (other.co_argcount, other.co_varnames))


def getObject(module, name, reload=0, modules={}):

    if modules.has_key(module):
        old=modules[module]
        if old.has_key(name) and not reload: return old[name]
    else:
        old=None
    
    d,n = path_split(module)
    if d: raise ValueError, (
        'The file name, %s, should be a simple file name' % module)

    execsrc=None

    d=find(n,'.')
    if d > 0:
        d,n=n[:d],n[d+1:]
        n=("%s/Products/%s/Extensions/%s.pyp" % (SOFTWARE_HOME,d,n))
        __traceback_info__=n, module
        if exists(n):
            data=zlib.decompress(
                rotor.newrotor(d+' shshsh').decrypt(open(n).read())
                )
            execsrc=compile(data,module,'exec')

    if execsrc is None:
        try: execsrc=open("%s/Extensions/%s.py" % (INSTANCE_HOME, module))
        except: raise "Module Error", (
            "The specified module, <em>%s</em>, couldn't be opened."
            % module)

    m={}
    exec execsrc in m

    try: r=m[name]
    except KeyError:
        raise 'Invalid Object Name', (
            "The specified object, <em>%s</em>, was not found in module, "
            "<em>%s</em>." % (name, module))

    if old:
        for k, v in m.items(): old[k]=v
    else: modules[module]=m

    return r

class NoBrains: pass

def getBrain(module, class_name, reload=0):
    'Check/load a class'

    if not module and not class_name: return NoBrains

    try: c=getObject(module, class_name, reload)
    except KeyError, v:
        if v == class_name: raise ValueError, (
            'The class, %s, is not defined in file, %s' % (class_name, module))

    if not hasattr(c,'__bases__'): raise ValueError, (
        '%s, is not a class' % class_name)
    
    return c
