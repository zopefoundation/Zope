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
'''Collect rules for access to objects that don\'t have roles.

The rules are expressed as a mapping from type -> assertion

An assertion can be:

  - A dict

  - A callable

  - Something with a truth value

If the assertion is a callable, then it will be called with
a name being accessed and the name used.  Its return value is ignored,
but in may veto an access by raising an exception.

If the assertion is a dictionary, then the keys are attribute names.
The values may be callables or objects with boolean values. If a value
is callable, it will be called with the object we are accessing an
attribute of and the attribute name. It should return an attribute
value. Callables are often used to returned guarded versions of
methods.  Otherwise, accesses are allowed if values in this dictionary
are true and disallowed if the values are false or if an item for an
attribute name is not present.

If the assertion is not a dict and is not callable, then access to
unprotected attributes is allowed if the assertion is true, and
disallowed otherwise.

XXX This descrition doesn't actually match what's done in ZopeGuards
or in ZopeSecurityPolicy. :(

$Id$'''

_noroles = [] # this is imported in various places

import Record

# Allow access to unprotected attributes
Record.Record.__allow_access_to_unprotected_subobjects__=1

# ContainerAssertions are used by cAccessControl to check access to
# attributes of container types, like dict, list, or string.
# ContainerAssertions maps types to a either a dict, a function, or a
# simple boolean value.  When guarded_getattr checks the type of its
# first argument against ContainerAssertions, and invokes checking
# logic depending on what value it finds.

# If the value for a type is:
#   - a boolean value:
#      - the value determines whether access is allowed
#   - a function (or callable):
#      - The function is called with the name of the attribute and
#        the actual attribute value, then the value is returned.
#        The function can raise an exception.
#   - a dict:
#      - The dict maps attribute names to boolean values or functions.
#        The boolean values behave as above, but the functions do not.
#        The value returned for attribute access is the result of
#        calling the function with the object and the attribute name.

ContainerAssertions={
    type(()): 1,
    type(''): 1,
    type(u''): 1,
    }

class _dummy_class: pass

from DocumentTemplate.DT_Util import TemplateDict
# Temporarily create a DictInstance so that we can mark its type as
# being a key in the ContainerAssertions.
templateDict = TemplateDict()
try:
    dictInstance = templateDict(dummy=1)[0]
    if type(dictInstance) is not type(_dummy_class()):
        ContainerAssertions[type(dictInstance)]=1
except:
    # Hmm, this may cause _() and _.namespace() to fail.
    # What to do?
    pass

Containers = ContainerAssertions.get

def allow_type(Type, allowed=1):
    """Allow a type and all of its methods and attributes to be used from
    restricted code.  The argument Type must be a type."""
    if type(Type) is not type:
        raise ValueError, "%s is not a type" % `Type`
    if hasattr(Type, '__roles__'):
        raise ValueError, "%s handles its own security" % `Type`
    if not (isinstance(allowed, int) or isinstance(allowed, dict)):
        raise ValueError, "The 'allowed' argument must be an int or dict."
    ContainerAssertions[Type] = allowed

#
#   WAAAA!
#
from BTrees.OOBTree import OOBTree, OOBucket, OOSet
from BTrees.OIBTree import OIBTree, OIBucket, OISet
from BTrees.IOBTree import IOBTree, IOBucket, IOSet
from BTrees.IIBTree import IIBTree, IIBucket, IISet

for tree_type, has_values in [(OOBTree, 1),
                              (OOBucket, 1),
                              (OOSet, 0),
                              (OIBTree, 1),
                              (OIBucket, 1),
                              (OISet, 0),
                              (IOBTree, 1),
                              (IOBucket, 1),
                              (IOSet, 0),
                              (IIBTree, 1),
                              (IIBucket, 1),
                              (IISet, 0),
                             ]:
    tree = tree_type()
    key_type = type(tree.keys())

    if key_type is not list: # lists have their own declarations
        allow_type(key_type)

    if has_values:
        assert key_type is type(tree.values())
        assert key_type is type(tree.items())
