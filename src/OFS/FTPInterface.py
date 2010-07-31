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
"""FTP Support for Zope classes.

Preliminary FTP support interface. Note, most FTP functions are
provided by existing methods such as PUT and manage_delObjects.

All FTP methods should be governed by a single permission:
'FTP access'.
"""

from zope.interface import implements

from interfaces import IFTPAccess


class FTPInterface:

    "Interface for FTP objects"

    implements(IFTPAccess)

    # XXX The stat and list marshal format should probably
    #     be XML, not marshal, maybe Andrew K's xml-marshal.
    #     This will probably be changed later.

    def manage_FTPstat(self,REQUEST):
        """Returns a stat-like tuple. (marshalled to a string) Used by
        FTP for directory listings, and MDTM and SIZE"""

    def manage_FTPlist(self,REQUEST):
        """Returns a directory listing consisting of a tuple of
        (id,stat) tuples, marshaled to a string. Note, the listing it
        should include '..' if there is a Folder above the current
        one.

        In the case of non-foldoid objects it should return a single
        tuple (id,stat) representing itself."""

    # Optional method to support FTP download.
    # Should not be implemented by Foldoid objects.

    def manage_FTPget(self):
        """Returns the source content of an object. For example, the
        source text of a Document, or the data of a file."""
