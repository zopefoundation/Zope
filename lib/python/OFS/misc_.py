##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

from App.ImageFile import ImageFile


class misc_:
    "Miscellaneous product information"
    __roles__=None

class p_:
    "Shared system information"
    __roles__=None
    
    broken=ImageFile('www/broken.gif', globals())

    User_icon =ImageFile('AccessControl/www/User_icon.gif')

    locked=ImageFile('www/modified.gif', globals())
    lockedo=ImageFile('www/locked.gif', globals())

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
    VersionManagement_icon=ImageFile('App/www/vManage.gif')
    DebugManager_icon=ImageFile('App/www/DebugManager_icon.gif')
    InstalledProduct_icon=ImageFile('App/www/installedProduct.gif')
    BrokenProduct_icon=ImageFile('App/www/brokenProduct.gif')
    Product_icon=ImageFile('App/www/product.gif')
    Factory_icon=ImageFile('App/www/factory.gif')
    Permission_icon=ImageFile('App/www/permission.gif')
    ProductFolder_icon=ImageFile('App/www/productFolder.gif')
    PyPoweredSmall_Gif=ImageFile('App/www/PythonPoweredSmall.gif')

    ZopeButton=ImageFile('App/www/zope_button.jpg')
    ZButton=ImageFile('App/www/z_button.jpg')
    zopelogo_jpg=ImageFile('www/zopelogo.jpg', globals())

    Properties_icon=ImageFile('OFS/www/Properties_icon.gif')
    Methods_icon=ImageFile('ZClasses/methods.gif')
    Propertysheets_icon=ImageFile('ZClasses/propertysheets.gif')

    ProductHelp_icon=ImageFile('HelpSys/images/productHelp.gif')
    HelpTopic_icon=ImageFile('HelpSys/images/helpTopic.gif')

class Misc_:
    "Miscellaneous product information"

    __roles__=None

    def __init__(self, name, dict):
        self._d=dict
        self.__name__=name

    def __str__(self): return self.__name__
    def __getitem__(self, name): return self._d[name]
    def __setitem__(self, name, v): self._d[name]=v
