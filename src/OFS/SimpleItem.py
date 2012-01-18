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

import marshal
import re
import sys
import time

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.Permissions import view as View
from AccessControl.unauthorized import Unauthorized
from AccessControl.ZopeSecurityPolicy import getRoles
from Acquisition import Acquired
from Acquisition import aq_acquire
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition import Implicit
from App.Management import Tabs
from App.special_dtml import HTML
from App.special_dtml import DTMLFile
from App.Undo import UndoSupport
from ComputedAttribute import ComputedAttribute
from DocumentTemplate.html_quote import html_quote
from DocumentTemplate.ustr import ustr
from ExtensionClass import Base
from Persistence import Persistent
from webdav.Resource import Resource
from webdav.xmltools import escape as xml_escape
from zExceptions import Redirect
from zExceptions.ExceptionFormatter import format_exception
from zope.interface import implements

from OFS.interfaces import IItem
from OFS.interfaces import IItemWithName
from OFS.interfaces import ISimpleItem
from OFS.owner import Owned
from OFS.CopySupport import CopySource
from OFS.role import RoleManager
from OFS.Traversable import Traversable
from OFS.ZDOM import Element

import logging
logger = logging.getLogger()

class Item(Base,
           Resource,
           CopySource,
           Tabs,
           Traversable,
           Element,
           Owned,
           UndoSupport,
           ):
    """A common base class for simple, non-container objects."""

    implements(IItem)

    security = ClassSecurityInfo()

    isPrincipiaFolderish=0
    isTopLevelPrincipiaApplicationObject=0

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
    id=''

    security.declarePublic('getId')
    def getId(self):
        """Return the id of the object as a string.

        This method should be used in preference to accessing an id attribute
        of an object directly. The getId method is public.
        """
        name=getattr(self, 'id', None)
        if callable(name):
            return name()
        if name is not None:
            return name
        if hasattr(self, '__name__'):
            return self.__name__
        raise AttributeError, 'This object has no id'

    # Alias id to __name__, which will make tracebacks a good bit nicer:
    __name__=ComputedAttribute(lambda self: self.getId())

    # Name, relative to BASEPATH1 of icon used to display item
    # in folder listings.
    icon=''

    # Meta type used for selecting all objects of a given type.
    meta_type='simple item'

    # Default title.
    title=''

    # Default propertysheet info:
    __propsets__=()

    manage_options=(
        UndoSupport.manage_options
        + Owned.manage_options
        + ({'label': 'Interfaces',
            'action': 'manage_interfaces'},)
        )

    # Attributes that must be acquired
    REQUEST = Acquired

    # Allow (reluctantly) access to unprotected attributes
    __allow_access_to_unprotected_subobjects__=1

    def title_or_id(self):
        """Return the title if it is not blank and the id otherwise.
        """
        title=self.title
        if callable(title):
            title=title()
        if title: return title
        return self.getId()

    def title_and_id(self):
        """Return the title if it is not blank and the id otherwise.

        If the title is not blank, then the id is included in parens.
        """
        title=self.title
        if callable(title):
            title=title()
        id = self.getId()
        return title and ("%s (%s)" % (title,id)) or id

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
        return apply(self._manage_editedDialog,(self, REQUEST), args)

    def raise_standardErrorMessage(
        self, client=None, REQUEST={},
        error_type=None, error_value=None, tb=None,
        error_tb=None, error_message='',
        tagSearch=re.compile(r'[a-zA-Z]>').search,
        error_log_url=''):

        try:
            if error_type  is None: error_type =sys.exc_info()[0]
            if error_value is None: error_value=sys.exc_info()[1]

            # allow for a few different traceback options
            if tb is None and error_tb is None:
                tb=sys.exc_info()[2]
            if type(tb) is not str and (error_tb is None):
                error_tb = pretty_tb(error_type, error_value, tb)
            elif type(tb) is str and not error_tb:
                error_tb = tb

            if hasattr(self, '_v_eek'):
                # Stop if there is recursion.
                raise error_type, error_value, tb
            self._v_eek = 1

            if hasattr(error_type, '__name__'):
                error_name = error_type.__name__
            else:
                error_name = 'Unknown'

            if not error_message:
                try:
                    s = ustr(error_value)
                except:
                    s = error_value
                try:
                    match = tagSearch(s)
                except TypeError:
                    match = None
                if match is not None:
                    error_message=error_value

            if client is None:
                client = self

            if not REQUEST:
                REQUEST = aq_acquire(self, 'REQUEST')

            try:
                s = aq_acquire(client, 'standard_error_message')

                # For backward compatibility, we pass 'error_name' as
                # 'error_type' here as historically this has always
                # been a string.
                kwargs = {'error_type': error_name,
                          'error_value': error_value,
                          'error_tb': error_tb,
                          'error_traceback': error_tb,
                          'error_message': xml_escape(str(error_message)),
                          'error_log_url': error_log_url}

                if getattr(aq_base(s), 'isDocTemp', 0):
                    v = s(client, REQUEST, **kwargs)
                elif callable(s):
                    v = s(**kwargs)
                else:
                    v = HTML.__call__(s, client, REQUEST, **kwargs)
            except:
                logger.error(
                    'Exception while rendering an error message',
                    exc_info=True
                    )
                try:
                    strv = repr(error_value) # quotes tainted strings
                except:
                    strv = ('<unprintable %s object>' % 
                            str(type(error_value).__name__))
                v = strv + (
                    (" (Also, the following error occurred while attempting "
                     "to render the standard error message, please see the "
                     "event log for full details: %s)")%(
                    html_quote(sys.exc_info()[1]),
                    ))

            # If we've been asked to handle errors, just return the rendered
            # exception and let the ZPublisher Exception Hook deal with it.
            return error_type, v, tb
        finally:
            if hasattr(self, '_v_eek'): del self._v_eek
            tb = None

    def manage(self, URL1):
        """
        """
        raise Redirect, "%s/manage_main" % URL1

    # This keeps simple items from acquiring their parents
    # objectValues, etc., when used in simple tree tags.
    def objectValues(self, spec=None):
        return ()
    objectIds=objectItems=objectValues

    # FTP support methods

    def manage_FTPstat(self,REQUEST):
        """Psuedo stat, used by FTP for directory listings.
        """
        from AccessControl.User import nobody
        mode=0100000

        if (hasattr(aq_base(self),'manage_FTPget')):
            try:
                if getSecurityManager().validate(
                    None, self, 'manage_FTPget', self.manage_FTPget):
                    mode=mode | 0440
            except Unauthorized:
                pass

            if nobody.allowed(
                self.manage_FTPget,
                getRoles(self, 'manage_FTPget', self.manage_FTPget, ()),
                ):
                mode=mode | 0004

        # check write permissions
        if hasattr(aq_base(self),'PUT'):
            try:
                if getSecurityManager().validate(None, self, 'PUT', self.PUT):
                    mode=mode | 0220
            except Unauthorized:
                pass

            if nobody.allowed(
                self.PUT,
                getRoles(self, 'PUT', self.PUT, ()),
                ):
                mode=mode | 0002

        # get size
        if hasattr(aq_base(self), 'get_size'):
            size=self.get_size()
        elif hasattr(aq_base(self),'manage_FTPget'):
            size=len(self.manage_FTPget())
        else:
            size=0
        # get modification time
        if hasattr(aq_base(self), 'bobobase_modification_time'):
            mtime=self.bobobase_modification_time().timeTime()
        else:
            mtime=time.time()
        # get owner and group
        owner=group='Zope'
        if hasattr(aq_base(self), 'get_local_roles'):
            for user, roles in self.get_local_roles():
                if 'Owner' in roles:
                    owner=user
                    break
        return marshal.dumps((mode,0,0,1,owner,group,size,mtime,mtime,mtime))

    def manage_FTPlist(self,REQUEST):
        """Directory listing for FTP.

        In the case of non-Foldoid objects, the listing should contain one
        object, the object itself.
        """
        from App.Common import is_acquired
        # check to see if we are being acquiring or not
        ob=self
        while 1:
            if is_acquired(ob):
                raise ValueError('FTP List not supported on acquired objects')
            if not hasattr(ob,'aq_parent'):
                break
            ob = aq_parent(ob)

        stat=marshal.loads(self.manage_FTPstat(REQUEST))
        id = self.getId()
        return marshal.dumps((id,stat))

    def __len__(self):
        return 1

    def __repr__(self):
        """Show the physical path of the object and its context if available.
        """
        try:
            path = '/'.join(self.getPhysicalPath())
        except:
            return Base.__repr__(self)
        context_path = None
        context = aq_parent(self)
        container = aq_parent(aq_inner(self))
        if aq_base(context) is not aq_base(container):
            try:
                context_path = '/'.join(context.getPhysicalPath())
            except:
                context_path = None
        res = '<%s' % self.__class__.__name__
        res += ' at %s' % path
        if context_path:
            res += ' used for %s' % context_path
        res += '>'
        return res

InitializeClass(Item)


class Item_w__name__(Item):

    """Mixin class to support common name/id functions"""

    implements(IItemWithName)

    def getId(self):
        """Return the id of the object as a string.
        """
        return self.__name__

    def title_or_id(self):
        """Return the title if it is not blank and the id otherwise.
        """
        return self.title or self.__name__

    def title_and_id(self):
        """Return the title if it is not blank and the id otherwise.

        If the title is not blank, then the id is included in parens.
        """
        t=self.title
        return t and ("%s (%s)" % (t,self.__name__)) or self.__name__

    def _setId(self, id):
        self.__name__=id

    def getPhysicalPath(self):
        """Get the physical path of the object.

        Returns a path (an immutable sequence of strings) that can be used to
        access this object again later, for example in a copy/paste operation.
        getPhysicalRoot() and getPhysicalPath() are designed to operate
        together.
        """
        path = (self.__name__,)

        p = aq_parent(aq_inner(self))
        if p is not None:
            path = p.getPhysicalPath() + path

        return path


def pretty_tb(t, v, tb, as_html=1):
    tb = format_exception(t, v, tb, as_html=as_html)
    tb = '\n'.join(tb)
    return tb


class SimpleItem(Item,
                 Persistent,
                 Implicit,
                 RoleManager,
                 ):

    # Blue-plate special, Zope Masala
    """Mix-in class combining the most common set of basic mix-ins
    """

    implements(ISimpleItem)

    security = ClassSecurityInfo()
    security.setPermissionDefault(View, ('Manager',))

    manage_options=Item.manage_options+(
        {'label': 'Security', 'action': 'manage_access'},
        )

InitializeClass(SimpleItem)
