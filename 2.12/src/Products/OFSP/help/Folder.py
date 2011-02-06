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


def manage_addFolder(id, title):
    """
    Add a Folder to the current ObjectManager

    Permission -- 'Add Folders'
    """


class Folder:
    """

    A Folder is a generic container object in Zope.

    Folders are the most common ObjectManager subclass in Zope.

    """

    __extends__=(
        'OFSP.ObjectManagerItem.ObjectManagerItem',
        'OFSP.ObjectManager.ObjectManager',
        'OFSP.PropertyManager.PropertyManager',
        )

    __constructor__ = manage_addFolder
