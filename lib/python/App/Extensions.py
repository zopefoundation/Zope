##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__='''Standard routines for handling extensions.

Extensions currently include external methods and pluggable brains.

$Id$'''
__version__='$Revision: 1.23 $'[11:-2]

import os, zlib, imp
import Products
from zExceptions import NotFound
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

    The search takes on multiple homes which are the instance home,
    the directory containing the directory containing the software
    home, and possibly product areas.
    """
    d,n = path_split(name)
    if d: raise ValueError, (
        'The file name, %s, should be a simple file name' % name)

    if checkProduct:
        l = name.find('.')
        if l > 0:
            p = name[:l]
            n = name[l + 1:]
            for product_dir in Products.__path__:
                r = _getPath(product_dir, os.path.join(p, prefix), n, suffixes)
                if r is not None: return r

    import App.config
    cfg = App.config.getConfiguration()
    sw=os.path.dirname(os.path.dirname(cfg.softwarehome))
    for home in (cfg.instancehome, sw):
        r=_getPath(home, prefix, name, suffixes)
        if r is not None: return r

def getObject(module, name, reload=0,
              # The use of a mutable default is intentional here,
              # because modules is a module cache.
              modules={}
              ):

    # The use of modules here is not thread safe, however, there is
    # no real harm in a race condition here.  If two threads
    # update the cache, then one will have simply worked a little
    # harder than need be.  So, in this case, we won't incur
    # the expense of a lock.
    old = modules.get(module)
    if old is not None and name in old and not reload:
        return old[name]

    base, ext = os.path.splitext(module)
    if ext in ('py', 'pyp', 'pyc'):
        # XXX should never happen; splitext() keeps '.' with the extension
        p = base
    else:
        p = module
    p=getPath('Extensions', p, suffixes=('','py','pyp','pyc'))
    if p is None:
        raise NotFound, (
            "The specified module, <em>%s</em>, couldn't be found." % module)

    __traceback_info__=p, module

    base, ext = os.path.splitext(p)
    if ext=='.pyc':
        file = open(p, 'rb')
        binmod=imp.load_compiled('Extension', p, file)
        file.close()
        m=binmod.__dict__

    elif ext=='.pyp':
        import rotor
        prod_id=module.split('.', 1)[0]
        data=zlib.decompress(
            rotor.newrotor(prod_id +' shshsh').decrypt(open(p,'rb').read())
            )
        execsrc=compile(data, module, 'exec')
        m={}
        exec execsrc in m

    else:
        try: execsrc=open(p)
        except: raise NotFound, (
            "The specified module, <em>%s</em>, couldn't be opened."
            % module)
        m={}
        exec execsrc in m

    if old is not None:
        old.update(m)
    else:
        modules[module] = m

    try:
        return m[name]
    except KeyError:
        raise NotFound, (
            "The specified object, <em>%s</em>, was not found in module, "
            "<em>%s</em>." % (name, module))

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
