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


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on App.Management.Navigation
class INavigation(Interface):

    """Basic navigation UI support"""

    manage = Attribute(""" """)
    manage_menu = Attribute(""" """)
    manage_top_frame = Attribute(""" """)
    manage_page_header = Attribute(""" """)
    manage_page_footer = Attribute(""" """)
    manage_form_title = Attribute("""Add Form""")
    zope_quick_start = Attribute(""" """)
    manage_copyright = Attribute(""" """)
    manage_zmi_prefs = Attribute(""" """)

    def manage_zmi_logout(REQUEST, RESPONSE):
        """Logout current user"""

INavigation.setTaggedValue('manage_page_style.css', Attribute(""" """))


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on App.PersistentExtra.PersistentUtil
class IPersistentExtra(Interface):

    def bobobase_modification_time():
        """
        """


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on App.Undo.UndoSupport
class IUndoSupport(Interface):

    manage_UndoForm = Attribute("""Manage Undo form""")

    def undoable_transactions(first_transaction=None,
                              last_transaction=None,
                              PrincipiaUndoBatchSize=None):
        """
        """

    def manage_undo_transactions(transaction_info=(), REQUEST=None):
        """
        """
