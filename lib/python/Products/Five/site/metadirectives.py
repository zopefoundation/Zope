##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Site support ZCML directive schemas

$Id: fivedirectives.py 18581 2005-10-14 16:54:25Z regebro $
"""
from zope.interface import Interface
from zope.configuration.fields import GlobalObject

class ILocalSiteDirective(Interface):
    """Make instances of class hookable for Site.

    site_class is an implementation of ISite, which will have it's methods
    monkey_patched into the the class. If not given a default implementation
    will be used.
    """
    class_ = GlobalObject(
        title=u"Class",
        required=True
        )

    site_class = GlobalObject(
        title=u"Site Class",
        required=False
        )
