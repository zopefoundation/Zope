############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
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
__doc__='''Sample application of the '__of__' protocol, computed attributes

It is not uncommon to wish to expose information via the attribute 
interface without exposing implementation.  In principle, one can 
use a custom '__getattr__' method to implement computed attributes,
however, this can be a bit cumbersome and can interfere with other
uses of '__getattr__', such as for persistence.

The '__of__' protocol provided by ExtensionClass provides another way
of implementing computed attribute.  The of '__of__' protocol provides
a way of returning sub-objects in the context of a container.  For
example::

   x.__of__(y)

should be interpreted as "compute y in the context of x".  When 
getting an ExtensionClass attribute, the attributes '__of__' method is
called automatically, if it has one.

This module provides a simple computed attribute implementation and
an example of its usage.

$Id: ComputedAttribute.py,v 1.2 1998/12/04 20:57:46 jim Exp $'''
__version__='$Revision: 1.2 $'[11:-2]

import ExtensionClass

class ComputedAttribute(ExtensionClass.Base):

    def __init__(self, func): self.func=func

    def __of__(self, parent): return self.func(parent)

############################################################################## 
# Test code:
#

if __name__ == "__main__":

    from math import sqrt

    class point(ExtensionClass.Base):

        def __init__(self, x, y): self.x, self.y = x, y

        radius=ComputedAttribute(lambda self: sqrt(self.x**2+self.y**2))

    p=point(2,2)
    print p.radius
