##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Things needed for backward compatibility
"""

import Acquisition


class AcquisitionBBB(object):
    """Emulate a class implementing Acquisition.interfaces.IAcquirer and
    IAcquisitionWrapper.
    """

    def __of__(self, context):
        # Technically this isn't in line with the way Acquisition's
        # __of__ works. With Acquisition, you get a wrapper around
        # the original object and only that wrapper's parent is the
        # new context.
        return self

    aq_self = aq_inner = aq_base = property(lambda self: self)
    aq_chain = property(Acquisition.aq_chain)
    aq_parent = property(Acquisition.aq_parent)

    def aq_acquire(self, *args, **kw):
        return Acquisition.aq_acquire(self, *args, **kw)

    def aq_inContextOf(self, *args, **kw):
        return Acquisition.aq_inContextOf(self, *args, **kw)
