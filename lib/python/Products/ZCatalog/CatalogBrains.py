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
        """Generate a URL for this record"""
        # XXX The previous implementation attempted to eat errors coming from
        #     REQUEST.physicalPathToURL. Unfortunately it also ate 
        #     ConflictErrors (from getPath), which is bad. Staring at the 
        #     relevent code in HTTPRequest.py it's unclear to me what could be 
        #     raised by it so I'm removing the exception handling here all 
        #     together. If undesired exceptions get raised somehow we should 
        #     avoid bare except band-aids and find a real solution.
        return self.REQUEST.physicalPathToURL(self.getPath(), relative)

    def getObject(self, REQUEST=None):
        """Return the object for this record
        
        Will return None if the object cannot be found via its cataloged path
        (i.e., it was deleted or moved without recataloging), or if the user is
        not authorized to access an object along the path.
        """
        return self.aq_parent.restrictedTraverse(self.getPath(), None)

    def getRID(self):
        """Return the record ID for this object."""
        return self.data_record_id_

class NoBrainer:
    """ This is an empty class to use when no brain is specified. """
    pass
