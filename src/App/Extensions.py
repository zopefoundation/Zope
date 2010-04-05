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
"""Standard routines for handling extensions.

Extensions currently include external methods and pluggable brains.
"""
import imp
import os

import Products
from zExceptions import NotFound


class FuncCode:

    def __init__(self, f, im=0):
        self.co_varnames = f.func_code.co_varnames[im:]
        self.co_argcount = f.func_code.co_argcount - im

    def __cmp__(self, other):
        if other is None:
            return 1
        try:
            return cmp((self.co_argcount, self.co_varnames),
                       (other.co_argcount, other.co_varnames))
        except:
            return 1


def _getPath(home, prefix, name, suffixes):

    dir = os.path.join(home, prefix)
    if dir == prefix:
        raise ValueError('The prefix, %s, should be a relative path' % prefix)

    fn = os.path.join(dir, name)
    if fn == name:
        # Paranoia
        raise ValueError('The file name, %s, should be a simple file name'
                            % name)

    for suffix in suffixes:
        if suffix:
            fqn = "%s.%s" % (fn, suffix)
        else:
            fqn = fn
        if os.path.exists(fqn):
            return fqn


def getPath(prefix, name, checkProduct=1, suffixes=('',), cfg=None):
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

      cfg -- ease testing (not part of the API)

    The search takes on multiple homes which are the instance home,
    the directory containing the directory containing the software
    home, and possibly product areas.
    """
    dir, ignored = os.path.split(name)
    if dir:
        raise ValueError('The file name, %s, should be a simple file name'
                            % name)

    result = None
    if checkProduct:
        dot = name.find('.')
        if dot > 0:
            product = name[:dot]
            extname = name[dot + 1:]
            for product_dir in Products.__path__:
                found = _getPath(product_dir, os.path.join(product, prefix),
                                 extname, suffixes)
                if found is not None:
                    return found

    if cfg is None:
        import App.config
        cfg = App.config.getConfiguration()

    if prefix == "Extensions" and getattr(cfg, 'extensions', None) is not None:
        found = _getPath(cfg.extensions, '', name, suffixes)
        if found is not None:
            return found

    locations = [cfg.instancehome]

    softwarehome = getattr(cfg, 'softwarehome', None)
    if softwarehome is not None:
        zopehome = os.path.dirname(softwarehome)
        locations.append(zopehome)

    for home in locations:
        found = _getPath(home, prefix, name, suffixes)
        if found is not None:
            return found

    try:
        dot = name.rfind('.')
        if dot > 0:
            realName = name[dot+1:]
            toplevel = name[:dot]
            
            rdot = toplevel.rfind('.')
            if rdot > -1:
                module = __import__(toplevel, globals(), {}, toplevel[rdot+1:])
            else:
                module = __import__(toplevel)
    
            prefix = os.path.join(module.__path__[0], prefix, realName)
            
            for suffix in suffixes:
                if suffix:
                    fn = "%s.%s" % (prefix, suffix)
                else:
                    fn = prefix
                if os.path.exists(fn): 
                    return fn
    except:
        pass
    

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
    if ext in ('py', 'pyc'):
        # XXX should never happen; splitext() keeps '.' with the extension
        prefix = base
    else:
        prefix = module

    path = getPath('Extensions', prefix, suffixes=('','py','pyc'))
    if path is None:
        raise NotFound("The specified module, '%s', couldn't be found."
                        % module)

    __traceback_info__= path, module

    base, ext = os.path.splitext(path)
    if ext=='.pyc':
        file = open(path, 'rb')
        binmod = imp.load_compiled('Extension', path, file)
        file.close()
        module_dict = binmod.__dict__
    else:
        try:
            execsrc = open(path)
        except:
            raise NotFound("The specified module, '%s', "
                           "couldn't be opened." % module)
        module_dict = {}
        exec execsrc in module_dict

    if old is not None:
        # XXX Accretive??
        old.update(module_dict)
    else:
        modules[module] = module_dict

    try:
        return module_dict[name]
    except KeyError:
        raise NotFound("The specified object, '%s', was not found "
                       "in module, '%s'." % (name, module))

class NoBrains:
    pass


def getBrain(module, class_name, reload=0, modules=None):
    """ Check/load a class from an extension.
    """
    if not module and not class_name:
        return NoBrains

    if modules is None:
        c=getObject(module, class_name, reload)
    else:
        c=getObject(module, class_name, reload, modules=modules)

    if getattr(c, '__bases__', None) is None:
        raise ValueError('%s, is not a class' % class_name)

    return c
