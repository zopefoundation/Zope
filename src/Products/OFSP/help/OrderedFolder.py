##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################


def manage_addOrderedFolder(id, title='', createPublic=0, createUserF=0,
                            REQUEST=None):
    """ Add a new ordered Folder object with id *id*.

    If the 'createPublic' and 'createUserF' parameters are set to any true
    value, an 'index_html' and a 'UserFolder' objects are created respectively
    in the new folder.
    """


class OrderedFolder:
    """ Extends the default Folder by order support.
    """

    __extends__ = ('OFSP.OrderSupport.OrderSupport', 'OFSP.Folder.Folder')

    __constructor__ = manage_addOrderedFolder
