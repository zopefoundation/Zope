##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__='''Objects that implement Permission-based roles.


$Id: PermissionRole.py,v 1.20 2003/11/28 16:43:53 jim Exp $'''
__version__='$Revision: 1.20 $'[11:-2]

_use_python_impl = 0
import os
if os.environ.get("ZOPE_SECURITY_POLICY", None) == "PYTHON":
    _use_python_impl = 1
else:
    try:
        # C Optimization:
        from cAccessControl import rolesForPermissionOn, \
             PermissionRole, imPermissionRole, _what_not_even_god_should_do
    except ImportError:
        # Fall back to Python implementation.
        _use_python_impl = 1


if 1 or _use_python_impl:

    import sys

    from ExtensionClass import Base

    import string

    name_trans=filter((lambda c, an=string.letters+string.digits+'_':
                       c not in an
                       ),
                      map(chr,range(256)))
    name_trans=string.maketrans(''.join(name_trans), '_'*len(name_trans))

    def rolesForPermissionOn(perm, obj, default=('Manager',), n=None):
        """Return the roles that have the given permission on the given object
        """

        n = n or '_'+string.translate(perm, name_trans)+"_Permission"
        r = None
        
        while 1:
            if hasattr(obj, n):
                roles = getattr(obj, n)
                if roles is None:
                    return 'Anonymous',

                t = type(roles)
                if t is tuple:
                    # If we get a tuple, then we don't acquire
                    if r is None:
                        return roles
                    return r+list(roles)

                if t is str:
                    # We found roles set to a name.  Start over
                    # with the new permission name.  If the permission
                    # name is '', then treat as private!
                    if roles:
                        if roles != n:
                            n = roles
                        # If we find a name that is the same as the
                        # current name, we just ignore it.
                        roles = None
                    else:
                        return _what_not_even_god_should_do

                elif roles:
                    if r is None:
                        r = list(roles)
                    else: r = r + list(roles)

            obj = getattr(obj, 'aq_inner', None)
            if obj is None:
                break
            obj = obj.aq_parent

        if r is None:
            return default

        return r

    class PermissionRole(Base):
        """Implement permission-based roles.

        Under normal circumstances, our __of__ method will be
        called with an unwrapped object.  The result will then be called
        with a wrapped object, if the original object was wrapped.
        To deal with this, we have to create an intermediate object.

        """

        def __init__(self, name, default=('Manager',)):
            self.__name__=name
            self._p='_'+string.translate(name,name_trans)+"_Permission"
            self._d = self.__roles__ = default

        def __of__(self, parent, getattr=getattr):
            r=imPermissionRole()
            r._p=self._p
            r._pa=parent
            r._d=self._d
            p=getattr(parent, 'aq_inner', None)
            if p is not None:
                return r.__of__(p)
            else:
                return r

        def rolesForPermissionOn(self, value):
            return rolesForPermissionOn(None, value, self._d, self._p)

    # This is used when a permission maps explicitly to no permission.
    _what_not_even_god_should_do=[]

    class imPermissionRole(Base):
        """Implement permission-based roles
        """

        def __of__(self, value):
            return rolesForPermissionOn(None, value, self._d, self._p)
        rolesForPermissionOn = __of__

        # The following methods are needed in the unlikely case that
        # an unwrapped object is accessed:
        
        def __getitem__(self, i):
            try:
                v=self._v
            except:
                v=self._v=self.__of__(self._pa)
                del self._pa

            return v[i]

        def __len__(self):
            try:
                v=self._v
            except:
                v=self._v=self.__of__(self._pa)
                del self._pa

            return len(v)

##############################################################################
# Test functions:
#

def main():
    # The "main" program for this module

    import sys
    sys.path.append('/projects/_/ExtensionClass')

    from Acquisition import Implicit
    class I(Implicit):
        x__roles__=PermissionRole('x')
        y__roles__=PermissionRole('y')
        z__roles__=PermissionRole('z')
        def x(self): pass
        def y(self): pass
        def z(self): pass



    a=I()
    a.b=I()
    a.b.c=I()
    a.q=I()
    a.q._x_Permission=('foo',)
    a._y_Permission=('bar',)
    a._z_Permission=('zee',)
    a.b.c._y_Permission=('Manage',)
    a.b._z_Permission=['also']

    print a.x.__roles__, list(a.x.__roles__)
    print a.b.x.__roles__
    print a.b.c.x.__roles__
    print a.q.x.__roles__
    print a.b.q.x.__roles__
    print a.b.c.q.x.__roles__
    print

    print a.y.__roles__, list(a.y.__roles__)
    print a.b.y.__roles__
    print a.b.c.y.__roles__
    print a.q.y.__roles__
    print a.b.q.y.__roles__
    print a.b.c.q.y.__roles__
    print

    print a.z.__roles__, list(a.z.__roles__)
    print a.b.z.__roles__
    print a.b.c.z.__roles__
    print a.q.z.__roles__
    print a.b.q.z.__roles__
    print a.b.c.q.z.__roles__
    print
