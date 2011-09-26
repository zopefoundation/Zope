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

from os.path import dirname

import AccessControl
from AccessControl.SecurityInfo import ClassSecurityInfo
import App
from App.class_init import InitializeClass
from App.ImageFile import ImageFile
import HelpSys
import OFS
import TreeDisplay
import webdav


class misc_:
    "Miscellaneous product information"
    security = ClassSecurityInfo()
    security.declareObjectPublic()

InitializeClass(misc_)


class p_:
    "Shared system information"
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    here = dirname(__file__)
    broken = ImageFile('www/broken.gif', here)

    User_icon = ImageFile('www/User_icon.gif', dirname(AccessControl.__file__))

    locked = ImageFile('www/modified.gif', here)
    lockedo = ImageFile('www/locked.gif', here)

    davlocked = ImageFile('www/davlock.gif', dirname(webdav.__file__))

    treedisplay_dir = dirname(TreeDisplay.__file__)
    pl = ImageFile('www/Plus_icon.gif', treedisplay_dir)
    mi = ImageFile('www/Minus_icon.gif', treedisplay_dir)

    app_dir = dirname(App.__file__)
    rtab = ImageFile('www/rtab.gif', app_dir)
    ltab = ImageFile('www/ltab.gif', app_dir)
    sp = ImageFile('www/sp.gif', app_dir)
    r_arrow_gif = ImageFile('www/r_arrow.gif', here)
    l_arrow_gif = ImageFile('www/l_arrow.gif', here)

    ofs_dir = dirname(OFS.__file__)
    ControlPanel_icon = ImageFile('www/ControlPanel_icon.gif', ofs_dir)
    ApplicationManagement_icon = ImageFile('www/cpSystem.gif', app_dir)
    DatabaseManagement_icon = ImageFile('www/dbManage.gif', app_dir)
    DebugManager_icon = ImageFile('www/DebugManager_icon.gif', app_dir)
    InstalledProduct_icon = ImageFile('www/installedProduct.gif', app_dir)
    BrokenProduct_icon = ImageFile('www/brokenProduct.gif', app_dir)
    Product_icon = ImageFile('www/product.gif', app_dir)
    Permission_icon = ImageFile('www/permission.gif', app_dir)
    ProductFolder_icon = ImageFile('www/productFolder.gif', app_dir)
    PyPoweredSmall_Gif = ImageFile('www/PythonPoweredSmall.gif', app_dir)

    ZopeButton = ImageFile('www/zope_button.jpg', app_dir)
    ZButton = ImageFile('www/z_button.jpg', app_dir)
    zopelogo_jpg = ImageFile('www/zopelogo.jpg', app_dir)

    Properties_icon = ImageFile('www/Properties_icon.gif', ofs_dir)
    Propertysheets_icon = ImageFile('www/Properties_icon.gif', ofs_dir)

    helpsys_dir = dirname(HelpSys.__file__)
    ProductHelp_icon=ImageFile('images/productHelp.gif', helpsys_dir)
    HelpTopic_icon=ImageFile('images/helpTopic.gif', helpsys_dir)

InitializeClass(p_)


class Misc_:
    "Miscellaneous product information"
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    def __init__(self, name, dict):
        self._d=dict
        self.__name__=name

    def __str__(self): return self.__name__
    def __getitem__(self, name): return self._d[name]
    def __setitem__(self, name, v): self._d[name]=v

InitializeClass(Misc_)
