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

from zope.interface import implements

import Acquisition
from Acquisition import aq_parent
import Record

from interfaces import ICatalogBrain


class AbstractCatalogBrain(Record.Record, Acquisition.Implicit):
    """Abstract base brain that handles looking up attributes as
    required, and provides just enough smarts to let us get the URL, path,
    and cataloged object without having to ask the catalog directly.
    """
    implements(ICatalogBrain)

    def has_key(self, key):
        return key in self.__record_schema__

    def __contains__(self, name):
        return name in self.__record_schema__

    def getPath(self):
        """Get the physical path for this record"""
        return aq_parent(self).getpath(self.data_record_id_)

    def getURL(self, relative=0):
        """Generate a URL for this record"""
        return self.REQUEST.physicalPathToURL(self.getPath(), relative)

    def _unrestrictedGetObject(self):
        """Return the object for this record

        Same as getObject, but does not do security checks.
        """
        return aq_parent(self).unrestrictedTraverse(self.getPath())

    def getObject(self, REQUEST=None):
        """Return the object for this record

        Will return None if the object cannot be found via its cataloged path
        (i.e., it was deleted or moved without recataloging), or if the user is
        not authorized to access the object.

        This method mimicks a subset of what publisher's traversal does,
        so it allows access if the final object can be accessed even
        if intermediate objects cannot.
        """
        path = self.getPath().split('/')
        if not path:
            return None
        parent = aq_parent(self)
        if len(path) > 1:
            parent = parent.unrestrictedTraverse(path[:-1])

        return parent.restrictedTraverse(path[-1])

    def getRID(self):
        """Return the record ID for this object."""
        return self.data_record_id_


class NoBrainer:
    """ This is an empty class to use when no brain is specified. """
    pass
