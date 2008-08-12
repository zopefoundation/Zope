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
__doc__='''Python Scripts Product Initialization
$Id$'''
__version__='$Revision: 1.13 $'[11:-2]

import PythonScript
try:
    import standard
except: pass

# Temporary
from Shared.DC import Scripts
__module_aliases__ = (
    ('Products.PythonScripts.Script', Scripts.Script),
    ('Products.PythonScripts.Bindings', Scripts.Bindings),
    ('Products.PythonScripts.BindingsUI', Scripts.BindingsUI),)

__roles__ = None
__allow_access_to_unprotected_subobjects__ = 1

def initialize(context):
    context.registerClass(
        PythonScript.PythonScript,
        permission='Add Python Scripts',
        constructors=(PythonScript.manage_addPythonScriptForm,
                      PythonScript.manage_addPythonScript),
        icon='www/pyscript.gif'
        )

    context.registerHelp()
    context.registerHelpTitle('Script (Python)')
    global _m
    _m['recompile'] = recompile
    _m['recompile__roles__'] = ('Manager',)

# utility stuff

def recompile(self):
    '''Recompile all Python Scripts'''
    base = self.this()
    scripts = base.ZopeFind(base, obj_metatypes=('Script (Python)',),
                            search_sub=1)
    names = []
    for name, ob in scripts:
        if ob._v_change:
            names.append(name)
            ob._compile()
            ob._p_changed = 1

    if names:
        return 'The following Scripts were recompiled:\n' + '\n'.join(names)
    return 'No Scripts were found that required recompilation.'


# Monkey patch for LP #257276

# This code is taken from the encodings module of Python 2.4.
# Note that this code is originally (C) CNRI and it is possibly not compatible
# with the ZPL and therefore should not live within svn.zope.org. However this
# checkin is blessed by Jim Fulton for now. The fix is no longer required with
# Python 2.5 and hopefully fixed in Python 2.4.6 release.



def search_function(encoding):

    # Cache lookup
    entry = _cache.get(encoding, _unknown)
    if entry is not _unknown:
        return entry

    # Import the module:
    #
    # First try to find an alias for the normalized encoding
    # name and lookup the module using the aliased name, then try to
    # lookup the module using the standard import scheme, i.e. first
    # try in the encodings package, then at top-level.
    #
    norm_encoding = normalize_encoding(encoding)
    aliased_encoding = _aliases.get(norm_encoding) or \
                       _aliases.get(norm_encoding.replace('.', '_'))
    if aliased_encoding is not None:
        modnames = [aliased_encoding,
                    norm_encoding]
    else:
        modnames = [norm_encoding]
    for modname in modnames:

        if not modname or '.' in modname:
            continue

        try:
            mod = __import__(modname,
                             globals(), locals(), _import_tail)
            if not mod.__name__.startswith('encodings.'):
                continue

        except ImportError:
            pass
        else:
            break
    else:
        mod = None

    try:
        getregentry = mod.getregentry
    except AttributeError:
        # Not a codec module
        mod = None

    if mod is None:
        # Cache misses
        _cache[encoding] = None
        return None

    # Now ask the module for the registry entry
    entry = tuple(getregentry())
    if len(entry) != 4:
        raise CodecRegistryError,\
              'module "%s" (%s) failed to register' % \
              (mod.__name__, mod.__file__)
    for obj in entry:
        if not callable(obj):
            raise CodecRegistryError,\
                  'incompatible codecs in module "%s" (%s)' % \
                  (mod.__name__, mod.__file__)

    # Cache the codec registry entry
    _cache[encoding] = entry

    # Register its aliases (without overwriting previously registered
    # aliases)
    try:
        codecaliases = mod.getaliases()
    except AttributeError:
        pass
    else:
        for alias in codecaliases:
            if not _aliases.has_key(alias):
                _aliases[alias] = modname

    # Return the registry entry
    return entry


# MONKEY

import encodings
encodings.search_function.func_code = search_function.func_code
