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

__version__ = "$Revision$"[11:-2]

from zope.interface import implements

import Acquisition, Record
from ZODB.POSException import ConflictError

from interfaces import ICatalogBrain

# Switch for new behavior, raise exception instead of returning None.
# Use 'catalog-getObject-raises off' in zope.conf to restore old behavior.
GETOBJECT_RAISES = True

class AbstractCatalogBrain(Record.Record, Acquisition.Implicit):
    """Abstract base brain that handles looking up attributes as
    required, and provides just enough smarts to let us get the URL, path,
    and cataloged object without having to ask the catalog directly.
    """
    implements(ICatalogBrain)
    
    def has_key(self, key):
        return self.__record_schema__.has_key(key)

    def getPath(self):
        """Get the physical path for this record"""
        return self.aq_parent.getpath(self.data_record_id_)

    def getURL(self, relative=0):
        """Generate a URL for this record"""
        # XXX The previous implementation attempted to eat errors coming from
        #     REQUEST.physicalPathToURL. Unfortunately it also ate 
        #     ConflictErrors (from getPath), which is bad. Staring at the 
        #     relevent code in HTTPRequest.py it's unclear to me what could be 
        #     raised by it so I'm removing the exception handling here all 
        #     together. If undesired exceptions get raised somehow we should 
        #     avoid bare except band-aids and find a real solution.
        return self.REQUEST.physicalPathToURL(self.getPath(), relative)

    def _unrestrictedGetObject(self):
        """Return the object for this record

        Same as getObject, but does not do security checks.
        """
        try:
            return self.aq_parent.unrestrictedTraverse(self.getPath())
        except ConflictError:
            raise
        except:
            if GETOBJECT_RAISES:
                raise
            return None

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
        parent = self.aq_parent
        if len(path) > 1:
            try:
                parent = parent.unrestrictedTraverse(path[:-1])
            except ConflictError:
                raise
            except:
                if GETOBJECT_RAISES:
                    raise
                return None

        try:
            target = parent.restrictedTraverse(path[-1])
        except ConflictError:
            raise
        except:
            if GETOBJECT_RAISES:
                raise
            return None

        return target

    def getRID(self):
        """Return the record ID for this object."""
        return self.data_record_id_

class NoBrainer:
    """ This is an empty class to use when no brain is specified. """
    pass
