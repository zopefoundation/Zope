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

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from App.ImageFile import ImageFile

class misc_:
    "Miscellaneous product information"
    security = ClassSecurityInfo()
    security.declareObjectPublic()

InitializeClass(misc_)

class p_:
    "Shared system information"
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    broken=ImageFile('www/broken.gif', globals())

    User_icon =ImageFile('AccessControl/www/User_icon.gif')

    locked=ImageFile('www/modified.gif', globals())
    lockedo=ImageFile('www/locked.gif', globals())

    davlocked=ImageFile('webdav/www/davlock.gif')

    pl=ImageFile('TreeDisplay/www/Plus_icon.gif')
    mi=ImageFile('TreeDisplay/www/Minus_icon.gif')
    rtab=ImageFile('App/www/rtab.gif')
    ltab=ImageFile('App/www/ltab.gif')
    sp  =ImageFile('App/www/sp.gif')
    r_arrow_gif=ImageFile('www/r_arrow.gif', globals())
    l_arrow_gif=ImageFile('www/l_arrow.gif', globals())

    ControlPanel_icon=ImageFile('OFS/www/ControlPanel_icon.gif')
    ApplicationManagement_icon=ImageFile('App/www/cpSystem.gif')
    DatabaseManagement_icon=ImageFile('App/www/dbManage.gif')
    DebugManager_icon=ImageFile('App/www/DebugManager_icon.gif')
    InstalledProduct_icon=ImageFile('App/www/installedProduct.gif')
    BrokenProduct_icon=ImageFile('App/www/brokenProduct.gif')
    Product_icon=ImageFile('App/www/product.gif')
    Permission_icon=ImageFile('App/www/permission.gif')
    ProductFolder_icon=ImageFile('App/www/productFolder.gif')
    PyPoweredSmall_Gif=ImageFile('App/www/PythonPoweredSmall.gif')

    ZopeButton=ImageFile('App/www/zope_button.jpg')
    ZButton=ImageFile('App/www/z_button.jpg')
    zopelogo_jpg=ImageFile('App/www/zopelogo.jpg')

    Properties_icon=ImageFile('OFS/www/Properties_icon.gif')
    Propertysheets_icon=ImageFile('OFS/www/Properties_icon.gif')

    ProductHelp_icon=ImageFile('HelpSys/images/productHelp.gif')
    HelpTopic_icon=ImageFile('HelpSys/images/helpTopic.gif')

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
