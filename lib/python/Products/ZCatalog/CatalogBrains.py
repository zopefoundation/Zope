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

__version__ = "$Revision$"[11:-2]

import Acquisition, Record
import zLOG
import sys

class AbstractCatalogBrain(Record.Record, Acquisition.Implicit):
    """Abstract base brain that handles looking up attributes as
    required, and provides just enough smarts to let us get the URL, path,
    and cataloged object without having to ask the catalog directly.
    """
    def has_key(self, key):
        return self.__record_schema__.has_key(key)

    def getPath(self):
        """Get the physical path for this record"""
        return self.aq_parent.getpath(self.data_record_id_)

    def getURL(self, relative=0):
        """Try to generate a URL for this record"""
        try:
            return self.REQUEST.physicalPathToURL(self.getPath(), relative)
        except:
            return self.getPath()

    def getObject(self, REQUEST=None):
        """Try to return the object for this record"""
        try:
            obj = self.aq_parent.unrestrictedTraverse(self.getPath())
            if not obj:
                if REQUEST is None:
                    REQUEST = self.REQUEST
                obj = self.aq_parent.resolve_url(self.getPath(), REQUEST)
            return obj
        except:
            zLOG.LOG('CatalogBrains', zLOG.INFO, 'getObject raised an error',
                     error=sys.exc_info())
            pass

    def getRID(self):
        """Return the record ID for this object."""
        return self.data_record_id_

class NoBrainer:
    """ This is an empty class to use when no brain is specified. """
    pass
