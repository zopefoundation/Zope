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

$Id: Extensions.py,v 1.6 1999/03/03 19:22:20 jim Exp $'''
__version__='$Revision: 1.6 $'[11:-2]

from string import find
import os, zlib, rotor
path_split=os.path.split
path_join=os.path.join
exists=os.path.exists
    
class FuncCode:

    def __init__(self, f, im=0):
        self.co_varnames=f.func_code.co_varnames[im:]
        self.co_argcount=f.func_code.co_argcount-im

    def __cmp__(self,other):
        if other is None: return 1
        try: return cmp((self.co_argcount, self.co_varnames),
                        (other.co_argcount, other.co_varnames))
        except: return 1


def _getPath(home, prefix, name, suffixes):
    d=path_join(home, prefix)
    if d==prefix: raise ValueError, (
        'The prefix, %s, should be a relative path' % prefix)
    d=path_join(d,name)
    if d==name: raise ValueError, ( # Paranoia
        'The file name, %s, should be a simple file name' % name)
    for s in suffixes:
        if s: s="%s.%s" % (d, s)
        else: s=d
        if exists(s): return s

def getPath(prefix, name, checkProduct=1, suffixes=('',)):
    """Find a file in one of several relative locations

    Arguments:

      prefix -- The location, relative to some home, to look for the
                file

      name -- The name of the file.  This must not be a path.

      checkProduct -- a flag indicating whether product directories
        should be used as additional hope ares to be searched. This
        defaults to a true value.

        If this is true and the name contains a dot, then the
        text before the dot is treated as a product name and
        the product package directory is used as anothe rhome.

      suffixes -- a sequences of file suffixes to check.
        By default, the name is used without a suffix.

    The search takes on multiple homes which are INSTANCE_HOME,
    the directory containing the directory containing SOFTWARE_HOME, and
    possibly product areas.     
    """
    d,n = path_split(name)
    if d: raise ValueError, (
        'The file name, %s, should be a simple file name' % name)

    sw=path_split(path_split(SOFTWARE_HOME)[0])[0]
    for home in (INSTANCE_HOME, sw):
        if checkProduct:
            l=find(name, '.')
            if l > 0:
                p=name[:l]
                n=name[l+1:]
                r=_getPath(home, "Products/%s/%s/" % (p,prefix),
                           n, suffixes)
                if r is not None: return r
        r=_getPath(home, prefix, name, suffixes)
        if r is not None: return r

def getObject(module, name, reload=0, modules={}):

    if modules.has_key(module):
        old=modules[module]
        if old.has_key(name) and not reload: return old[name]
    else:
        old=None

    if module[-3:]=='.py': p=module[:-3]
    elif module[-4:]=='.pyp': p=module[:-4]
    else: p=module
    p=getPath('Extensions', p, suffixes=('','py','pyp'))
    if p is None:
        raise "Module Error", (
            "The specified module, <em>%s</em>, couldn't be found.")

    __traceback_info__=p, module

    if p[-4:]=='.pyp':
        data=zlib.decompress(
            rotor.newrotor(d+' shshsh').decrypt(open(p).read())
            )
        execsrc=compile(data,module,'exec')
    else:
        try: execsrc=open(p)
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
