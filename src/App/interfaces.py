##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""App interfaces.
"""

from zope.interface import Attribute
from zope.interface import Interface


class INavigation(Interface):
    """Basic navigation UI support"""

    manage = Attribute(""" """)
    manage_menu = Attribute(""" """)
    manage_page_header = Attribute(""" """)
    manage_page_footer = Attribute(""" """)
    manage_form_title = Attribute("""Add Form""")

    def manage_zmi_logout(REQUEST, RESPONSE):
        """Logout current user"""


class ICSSPaths(Interface):
    """Paths to CSS resources needed for the ZMI."""


class IJSPaths(Interface):
    """Paths to JAvaScript resources needed for the ZMI."""
