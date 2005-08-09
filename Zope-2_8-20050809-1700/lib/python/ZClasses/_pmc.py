##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ZCLass Persistent Meta Class

IMPORTANT -- This module is private to ZClasses and experimetal.
             It is highly subject to change and likely to move

$Id$
"""
import ExtensionClass
import ZODB.persistentclass

# See the comments in ZODB.persistentclass

class ZClassPersistentMetaClass(ExtensionClass.ExtensionClass):

    # For weird reasons having to do with restrictions on built-in
    # types, we can't subclass
    # ZODB.persistentclass.PersistentMetaClass, so we do the next best
    # thing:

    for name in ('_p_jar', '_p_oid', '_p_changed', '_p_serial',
                 '__getnewargs__', '_p_maybeupdate', '_p_deactivate',
                 '_p_invalidate', '__getstate__', '_p_activate', ):
        locals()[name] = ZODB.persistentclass.PersistentMetaClass.__dict__[
            name]

    def __new__(self, name, bases, cdict, _p_changed=False):

        # _p_changed will be None if we are being loaded from the
        # database, because __getnewargs__ returns an extra argument
        # for _p_changed.

        # The above is *not* true for old (< 2.8) ZClass code.
        # Old ZClass records have all of their data in their
        # arguments.  This is rather fortunate.  It means that
        # we don't need to call __setstate__. We *do*, however, need
        # to call pmc_init_of.

        cdict = dict([(k, v) for (k, v) in cdict.items()
                      if not k.startswith('_p_')])
        cdict['_p_class_dict'] = {'_p_changed': _p_changed}
        result = super(ZClassPersistentMetaClass, self
                       ).__new__(self, name, bases, cdict)
        ExtensionClass.pmc_init_of(result)
        return result

    # copy_reg.py:_slotnames() tries to use this attribute as a cache.
    # Dont allow this attribute to be written as it may cause us
    # to register with the data_manager.
    __slotnames__ = property(None)

    def __setattr__(self, name, v):
        super(ZClassPersistentMetaClass, self).__setattr__(name, v)
        if not ((name.startswith('_p_') or name.startswith('_v'))):
            self._p_maybeupdate(name)

    def __delattr__(self, name):
        super(ZClassPersistentMetaClass, self).__delattr__(name)
        if not ((name.startswith('_p_') or name.startswith('_v'))):
            self._p_maybeupdate(name)
    
    def __setstate__(self, state):
        try:
            self.__bases__, cdict = state
        except TypeError:
            # Maybe an old ZClass with state == None
            if state is None:
                cdict = None

        if cdict is not None:
            cdict = dict([(k, v) for (k, v) in cdict.items()
                          if not k.startswith('_p_')])

            _p_class_dict = self._p_class_dict
            self._p_class_dict = {}

            to_remove = [
                k for k in self.__dict__
                if ((k not in cdict)
                    and
                    (k not in ZODB.persistentclass.special_class_descrs)
                    and
                    (k != '_p_class_dict')
                    )]

            for k in to_remove:
                delattr(self, k)
            
            try:
                del cdict['__slotnames__']
            except KeyError:
                pass

            for k, v in cdict.items():
                setattr(self, k, v)

            self._p_class_dict = _p_class_dict

        ExtensionClass.pmc_init_of(self)

        self._p_changed = False
        
    __setstate__ = ZODB.persistentclass._p_MethodDescr(__setstate__)
