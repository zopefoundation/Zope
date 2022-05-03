##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""This module implements a simple item mix-in for objects that have a
very simple (e.g. one-screen) management interface, like documents,
Aqueduct database adapters, etc.

This module can also be used as a simple template for implementing new
item types.
"""

import logging
import re
import sys

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import access_contents_information
from AccessControl.Permissions import view as View
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Acquired
from Acquisition import Implicit
from Acquisition import aq_acquire
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.Management import Navigation
from App.Management import Tabs
from App.special_dtml import HTML
from App.special_dtml import DTMLFile
from ComputedAttribute import ComputedAttribute
from DocumentTemplate.html_quote import html_quote
from DocumentTemplate.ustr import ustr
from ExtensionClass import Base
from OFS.CopySupport import CopySource
from OFS.interfaces import IItem
from OFS.interfaces import IItemWithName
from OFS.interfaces import ISimpleItem
from OFS.Lockable import LockableItem
from OFS.owner import Owned
from OFS.role import RoleManager
from OFS.Traversable import Traversable
from Persistence import Persistent
from webdav.Resource import Resource
from zExceptions import Redirect
from zExceptions.ExceptionFormatter import format_exception
from zope.interface import implementer
from ZPublisher.HTTPRequest import default_encoding


logger = logging.getLogger()


class PathReprProvider(Base):
    """Provides a representation that includes the physical path.

    Should be in the MRO before persistent.Persistent as this provides an own
    implementation of `__repr__` that includes information about connection and
    oid.
    """

    def __repr__(self):
        """Show the physical path of the object and context if available."""
        try:
            path = '/'.join(self.getPhysicalPath())
        except Exception:
            return super().__repr__()
        context_path = None
        context = aq_parent(self)
        container = aq_parent(aq_inner(self))
        if aq_base(context) is not aq_base(container):
            try:
                context_path = '/'.join(context.getPhysicalPath())
            except Exception:
                context_path = None
        res = '<%s' % self.__class__.__name__
        res += ' at %s' % path
        if context_path:
            res += ' used for %s' % context_path
        res += '>'
        return res


@implementer(IItem)
class Item(
    PathReprProvider,
    Base,
    Navigation,
    Resource,
    LockableItem,
    CopySource,
    Tabs,
    Traversable,
    Owned
):
    """A common base class for simple, non-container objects."""

    zmi_icon = 'far fa-file'
    zmi_show_add_dialog = True

    security = ClassSecurityInfo()

    isPrincipiaFolderish = 0
    isTopLevelPrincipiaApplicationObject = 0

    manage_options = ({'label': 'Interfaces', 'action': 'manage_interfaces'},)

    def manage_afterAdd(self, item, container):
        pass
    manage_afterAdd.__five_method__ = True

    def manage_beforeDelete(self, item, container):
        pass
    manage_beforeDelete.__five_method__ = True

    def manage_afterClone(self, item):
        pass
    manage_afterClone.__five_method__ = True

    # Direct use of the 'id' attribute is deprecated - use getId()
    id = ''

    @security.public
    def getId(self):
        """Return the id of the object as a string.

        This method should be used in preference to accessing an id attribute
        of an object directly. The getId method is public.
        """
        name = self.id
        if name is not None:
            return name
        return self.__name__

    # Alias id to __name__, which will make tracebacks a good bit nicer:
    __name__ = ComputedAttribute(lambda self: self.id)

    # Meta type used for selecting all objects of a given type.
    meta_type = 'simple item'

    # Default title.
    title = ''

    # Default propertysheet info:
    __propsets__ = ()

    # Attributes that must be acquired
    REQUEST = Acquired

    # Allow (reluctantly) access to unprotected attributes
    __allow_access_to_unprotected_subobjects__ = 1

    def title_or_id(self):
        """Return the title if it is not blank and the id otherwise.
        """
        title = self.title
        if callable(title):
            title = title()
        if title:
            return title
        return self.getId()

    def title_and_id(self):
        """Return the title if it is not blank and the id otherwise.

        If the title is not blank, then the id is included in parens.
        """
        title = self.title
        if callable(title):
            title = title()
        id = self.getId()
        # Make sure we don't blindly concatenate encoded and unencoded data
        if title and type(id) is not type(title):
            if isinstance(id, bytes):
                id = id.decode(default_encoding)
            if isinstance(title, bytes):
                title = title.decode(default_encoding)
        return title and f"{title} ({id})" or id

    def this(self):
        # Handy way to talk to ourselves in document templates.
        return self

    def tpURL(self):
        # My URL as used by tree tag
        return self.getId()

    def tpValues(self):
        # My sub-objects as used by the tree tag
        return ()

    _manage_editedDialog = DTMLFile('dtml/editedDialog', globals())

    def manage_editedDialog(self, REQUEST, **args):
        return self._manage_editedDialog(self, REQUEST, **args)

    def raise_standardErrorMessage(
        self,
        client=None,
        REQUEST={},
        error_type=None,
        error_value=None,
        tb=None,
        error_tb=None,
        error_message='',
        tagSearch=re.compile(r'[a-zA-Z]>').search,
        error_log_url=''
    ):

        try:
            if error_type is None:
                error_type = sys.exc_info()[0]
            if error_value is None:
                error_value = sys.exc_info()[1]

            # allow for a few different traceback options
            if tb is None and error_tb is None:
                tb = sys.exc_info()[2]
            if not isinstance(tb, str) and (error_tb is None):
                error_tb = pretty_tb(error_type, error_value, tb)
            elif isinstance(tb, str) and not error_tb:
                error_tb = tb

            if hasattr(self, '_v_eek'):
                # Stop if there is recursion.
                raise error_value.with_traceback(tb)
            self._v_eek = 1

            if hasattr(error_type, '__name__'):
                error_name = error_type.__name__
            else:
                error_name = 'Unknown'

            if not error_message:
                try:
                    s = ustr(error_value)
                except Exception:
                    s = error_value
                try:
                    match = tagSearch(s)
                except TypeError:
                    match = None
                if match is not None:
                    error_message = error_value

            if client is None:
                client = self

            if not REQUEST:
                REQUEST = aq_acquire(self, 'REQUEST')

            try:
                s = aq_acquire(client, 'standard_error_message')

                # For backward compatibility, we pass 'error_name' as
                # 'error_type' here as historically this has always
                # been a string.
                kwargs = {
                    'error_type': error_name,
                    'error_value': error_value,
                    'error_tb': error_tb,
                    'error_traceback': error_tb,
                    'error_message': error_message,
                    'error_log_url': error_log_url,
                }

                if getattr(aq_base(s), 'isDocTemp', 0):
                    v = s(client, REQUEST, **kwargs)
                elif callable(s):
                    v = s(**kwargs)
                else:
                    v = HTML.__call__(s, client, REQUEST, **kwargs)
            except Exception:
                logger.error(
                    'Exception while rendering an error message',
                    exc_info=True
                )
                try:
                    strv = repr(error_value)  # quotes tainted strings
                except Exception:
                    strv = ('<unprintable %s object>' %
                            str(type(error_value).__name__))
                v = strv + (
                    (" (Also, the following error occurred while attempting "
                     "to render the standard error message, please see the "
                     "event log for full details: %s)") % (
                        html_quote(sys.exc_info()[1]),
                    ))

            # If we've been asked to handle errors, just return the rendered
            # exception and let the ZPublisher Exception Hook deal with it.
            return error_type, v, tb
        finally:
            if hasattr(self, '_v_eek'):
                del self._v_eek
            tb = None

    def manage(self, URL1):
        """
        """
        raise Redirect("%s/manage_main" % URL1)

    # This keeps simple items from acquiring their parents
    # objectValues, etc., when used in simple tree tags.
    def objectValues(self, spec=None):
        return ()
    objectIds = objectItems = objectValues

    def __len__(self):
        return 1

    @security.protected(access_contents_information)
    def getParentNode(self):
        """The parent of this node.  All nodes except Document
        DocumentFragment and Attr may have a parent"""
        return getattr(self, '__parent__', None)


InitializeClass(Item)


@implementer(IItemWithName)
class Item_w__name__(Item):
    """Mixin class to support common name/id functions"""

    def getId(self):
        """Return the id of the object as a string.
        """
        return self.__name__

    # Alias (deprecated) `id` to `getId()` (but avoid recursion)
    id = ComputedAttribute(
        lambda self: self.getId() if "__name__" in self.__dict__ else "")

    def title_or_id(self):
        """Return the title if it is not blank and the id otherwise.
        """
        return self.title or self.__name__

    def title_and_id(self):
        """Return the title if it is not blank and the id otherwise.

        If the title is not blank, then the id is included in parens.
        """
        t = self.title
        return t and f"{t} ({self.__name__})" or self.__name__

    def _setId(self, id):
        self.__name__ = id

    def getPhysicalPath(self):
        # Get the physical path of the object.
        #
        # Returns a path (an immutable sequence of strings) that can be used
        # to access this object again later, for example in a copy/paste
        # operation.  getPhysicalRoot() and getPhysicalPath() are designed to
        # operate together.

        path = (self.__name__, )
        p = aq_parent(aq_inner(self))
        if p is not None:
            path = p.getPhysicalPath() + path
        return path


def pretty_tb(t, v, tb, as_html=1):
    tb = format_exception(t, v, tb, as_html=as_html)
    tb = '\n'.join(tb)
    return tb


@implementer(ISimpleItem)
class SimpleItem(
    Item,
    Persistent,
    Implicit,
    RoleManager,
):
    """Mix-in class combining the most common set of basic mix-ins
    """

    security = ClassSecurityInfo()
    security.setPermissionDefault(View, ('Manager',))

    manage_options = Item.manage_options + (
        {
            'label': 'Security',
            'action': 'manage_access',
        },
    )


InitializeClass(SimpleItem)
