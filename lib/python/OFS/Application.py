##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################
__doc__='''Application support


$Id: Application.py,v 1.80 1998/12/11 05:32:21 amos Exp $'''
__version__='$Revision: 1.80 $'[11:-2]


import Globals,Folder,os,regex,sys,App.Product, App.ProductRegistry
import time, rotor, marshal
from string import strip, lower, find, rfind, join
from DateTime import DateTime
from AccessControl.User import UserFolder
from HelpSys.HelpSys import HelpSys
from App.ApplicationManager import ApplicationManager
from Globals import Persistent
from FindSupport import FindSupport
from ImageFile import ImageFile
from urllib import quote


_standard_error_msg='''\
<!--#var standard_html_header-->
<!--#if error_message-->
 <!--#var error_message-->
<!--#else-->
<TABLE BORDER="0" WIDTH="100%">
<TR>
  <TD WIDTH="10%" ALIGN="CENTER">
  <STRONG><FONT SIZE="+6" COLOR="#77003B">!</FONT></STRONG>
  </TD>
  <TD WIDTH="90%"><BR>
  <FONT SIZE="+2">System Unavailable</FONT>
  <P>This site is currently experiencing technical difficulties. 
Please contact the site administrator for more information.  For
additional technical information, please refer to the HTML source for this
page.  Thank you for your patience.</P>
  </TD>
</TR>
</TABLE>
<!--
 Error type:  <!--#var error_type-->
 Error value: <!--#var error_value-->
 -->
<!--#comment-->
 Here, events like logging and other actions may also be performed, such as
 sending mail automatically to the administrator.
<!--#/comment-->
<!--#endif-->
<!--#var standard_html_footer-->'''


class Application(Globals.ApplicationDefaultPermissions, Folder.Folder,
                  App.ProductRegistry.ProductRegistry, FindSupport):
    """Top-level system object"""
    title    ='Zope'
    __roles__=['Manager', 'Anonymous']
    __defined_roles__=('Manager','Anonymous')
    web__form__method='GET'
    isTopLevelPrincipiaApplicationObject=1

    # Create the help system object
    HelpSys=HelpSys()
    
    class misc_:
        "Miscellaneous product information"
        __roles__=None

    class p_:
        "Shared system information"
        __roles__=None

        folder=ImageFile('www/Folder_icon.gif', globals())
        image =ImageFile('www/Image_icon.gif', globals())
        file  =ImageFile('www/File_icon.gif', globals())
        doc   =ImageFile('www/Document_icon.gif', globals())
        broken=ImageFile('www/broken.gif', globals())

        UserFolder=ImageFile('AccessControl/www/UserFolder_icon.gif')
        User_icon =ImageFile('AccessControl/www/User_icon.gif')

        locked=ImageFile('www/modified.gif', globals())
        lockedo=ImageFile('www/locked.gif', globals())

        pl=ImageFile('TreeDisplay/www/Plus_icon.gif')
        mi=ImageFile('TreeDisplay/www/Minus_icon.gif')
        rtab=ImageFile('App/www/rtab.gif')
        ltab=ImageFile('App/www/ltab.gif')
        ControlPanel_icon=ImageFile('OFS/www/ControlPanel_icon.gif')
        ApplicationManagement_icon=ImageFile('App/www/cpSystem.gif')
        DatabaseManagement_icon=ImageFile('App/www/dbManage.gif')
        InstalledProduct_icon=ImageFile('App/www/installedProduct.gif')
        Product_icon=ImageFile('App/www/product.gif')
        Factory_icon=ImageFile('App/www/factory.gif')
        ProductFolder_icon=ImageFile('App/www/productFolder.gif')
        PyPoweredSmall_Gif=ImageFile('App/www/PythonPoweredSmall.gif')

        #up=ImageFile('www/UpFolder_icon.gif', globals())
        #help=ImageFile('www/Help_icon.gif', globals())

    manage_options=(
    {'icon':'OFS/Folder_icon.gif', 'label':'Contents',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'OFS/Properties_icon.gif', 'label':'Properties',
     'action':'manage_propertiesForm',   'target':'manage_main'},
    {'icon':'', 'label':'Security',
     'action':'manage_access',   'target':'manage_main'},
    {'icon':'App/undo_icon.gif', 'label':'Undo',
     'action':'manage_UndoForm',   'target':'manage_main'},
    {'label':'Find', 'action':'manage_findFrame',
     'target':'manage_main'},
    )

    _reserved_names=('standard_html_header',
                     'standard_html_footer',
                     'standard_error_message',
                     'acl_users',
                     'Control_Panel')

    def _init(self):
        # Initialize users
        self.__allow_groups__=UserFolder()
        self._setObject('acl_users', self.__allow_groups__)

        # Initialize control panel
        cpl=ApplicationManager()
        cpl._init()
        self._setObject('Control_Panel', cpl)

        # Note that this may happen before products are
        # installed, so we have to use addDocument as stand-alone.
        import Document
        Document.manage_addDocument(
            self,
            'standard_html_header',
            'Standard Html Header',
            '<HTML><HEAD><TITLE><!--#var title_or_id-->' \
            '</TITLE></HEAD><BODY BGCOLOR="#FFFFFF">')
        Document.manage_addDocument(
            self,
            'standard_html_footer',
            'Standard Html Footer',
            '</BODY></HTML>')
        Document.manage_addDocument(
            self,
            'standard_error_message',
            'Standard Error Message',
            _standard_error_msg)




    def id(self):
        try:    return self.REQUEST['SCRIPT_NAME'][1:]
        except: return self.title

    def folderClass(self): return Folder.Folder

    def __class_init__(self): Globals.default__class_init__(self)

    def PrincipiaRedirect(self,destination,URL1):
        """Utility function to allow user-controlled redirects"""
        if find(destination,'//') >= 0: raise 'Redirect', destination
        raise 'Redirect', ("%s/%s" % (URL1, destination))
    Redirect=PrincipiaRedirect

    def __bobo_traverse__(self, REQUEST, name=None):
        if name is None and REQUEST.has_key(Globals.SessionNameName):
            pd=Globals.SessionBase[REQUEST[Globals.SessionNameName]]
            alternate_self=pd.jar[self._p_oid]
            if hasattr(self, 'aq_parent'):
                alternate_self=alternate_self.__of__(self.aq_parent)
            return alternate_self

        try:    self._p_jar.cache.incrgc() # Perform incremental GC
        except: pass

        try: return getattr(self, name)
        except AttributeError:
            try: return self[name]
            except KeyError:
                raise 'NotFound',(
                    "Sorry, the requested document does not exist.<p>"
                    "\n<!--\n%s\n%s\n-->" % (name,REQUEST['REQUEST_METHOD']))

    def PrincipiaTime(self, *args):
        """Utility function to return current date/time"""
        return apply(DateTime, args)


class Expired(Persistent):
    icon='p_/broken'

    def __setstate__(self, s={}):
        dict=self.__dict__
        if s.has_key('id'):
            dict['id']=s['id']
        elif s.has_key('__name__'):
            dict['id']=s['__name__']
        else: dict['id']='Unknown'
        dict['title']='** Expired **'

    def __save__(self):
        pass

    __inform_commit__=__save__



def open_bobobase():
    # Open the application database

    Bobobase=Globals.Bobobase=Globals.PickleDictionary(Globals.BobobaseName)

    product_dir=os.path.join(SOFTWARE_HOME,'Products')

    __traceback_info__=sys.path
    
    try: app=Bobobase['Application']
    except KeyError:
        app=Application()
        app._init()
        Bobobase['Application']=app
        get_transaction().commit()

    # The following items marked b/c are backward compatibility hacks
    # which make sure that expected system objects are added to the
    # bobobase. This is required because the bobobase in use may pre-
    # date the introduction of certain system objects such as those
    # which provide Lever support.

    # b/c: Ensure that Control Panel exists.
    if not hasattr(app, 'Control_Panel'):
        cpl=ApplicationManager()
        cpl._init()
        app._setObject('Control_Panel', cpl)
        get_transaction().commit()

    # b/c: Ensure that a ProductFolder exists.
    if not hasattr(app.Control_Panel.aq_base, 'Products'):
        app.Control_Panel.Products=App.Product.ProductFolder()
        get_transaction().commit()

    # b/c: Ensure that std err msg exists.
    if not hasattr(app, 'standard_error_message'):
        import Document
        Document.manage_addDocument(
            app,
            'standard_error_message',
            'Standard Error Message',
            _standard_error_msg)
        get_transaction().commit()

    install_products(app)
    get_transaction().commit()

    return Bobobase

def install_products(app):
    # Install a list of products into the basic folder class, so
    # that all folders know about top-level objects, aka products

    path_join=os.path.join
    product_dir=path_join(SOFTWARE_HOME,'Products')
    isdir=os.path.isdir
    exists=os.path.exists
    DictType=type({})

    from Folder import Folder
    folder_permissions={}
    for p in Folder.__ac_permissions__:
        permission, names = p[:2]
        folder_permissions[permission]=names

    meta_types=list(Folder.dynamic_meta_types)

    product_names=os.listdir(product_dir)
    product_names.sort()
    global_dict=globals()
    silly=('__doc__',)

    for product_name in product_names:
        package_dir=path_join(product_dir, product_name)
        if not isdir(package_dir): continue
        if not exists(path_join(package_dir, '__init__.py')):
            if not exists(path_join(package_dir, '__init__.pyc')):
                continue

        product=__import__("Products.%s" % product_name,
                           global_dict, global_dict, silly)

        permissions={}
        new_permissions={}
        for permission, names in pgetattr(product, '__ac_permissions__', ()):
            if names:
                for name in names: permissions[name]=permission
            elif not folder_permissions.has_key(permission):
                new_permissions[permission]=()

        for meta_type in pgetattr(product, 'meta_types', ()):
            if product_name=='OFSP': meta_types.insert(0,meta_type)
            else: meta_types.append(meta_type)
            name=meta_type['name']

        for name,method in pgetattr(product, 'methods', {}).items():
            if not hasattr(Folder, name):
                setattr(Folder, name, method)
                if name[-9:]=='__roles__': continue # Just setting roles
                if (permissions.has_key(name) and
                    not folder_permissions.has_key(permissions[name])):
                    permission=permissions[name]
                    if new_permissions.has_key(permission):
                        new_permissions[permission].append(name)
                    else:
                        new_permissions[permission]=[name]
        
        if new_permissions:
            new_permissions=new_permissions.items()
            for permission, names in new_permissions:
                folder_permissions[permission]=names
            new_permissions.sort()
            Folder.__dict__['__ac_permissions__']=tuple(
                list(Folder.__ac_permissions__)+new_permissions)
        
        misc_=pgetattr(product, 'misc_', {})
        if type(misc_) is DictType: misc_=Misc_(product_name, misc_)
        Application.misc_.__dict__[product_name]=misc_

        # Set up dynamic project information.
        App.Product.initializeProduct(product_name, package_dir, app)

    Folder.dynamic_meta_types=tuple(meta_types)

    Globals.default__class_init__(Folder)


def lcd(e):
    _k1_='\357\261\390\247\357\362\306\216\226'
    _k2_='\157\161\090\147\157\122\106\016\126'
    rot=rotor.newrotor(_k2_, 13)
    dat=rot.decrypt(e)
    del rot
    dat=list(dat)
    dat.reverse()
    dat=join(dat,'')
    dat=marshal.loads(dat)
    if type(dat) != type([]):
        # Compatibility w/old lic files
        rot=rotor.newrotor(_k1_, 13)
        dat=rot.decrypt(e)
        del rot
        dat=list(dat)
        dat.reverse()
        dat=join(dat,'')
        dat=marshal.loads(dat)
    if type(dat) != type([]):
        return None
    return dat


def pgetattr(product, name, default=install_products, __init__=0):
    if not __init__ and hasattr(product, name): return getattr(product, name)
    if hasattr(product, '__init__'):
        product=product.__init__
        if hasattr(product, name): return getattr(product, name)

    if default is not install_products: return default

    raise AttributeError, name

class Misc_:
    "Miscellaneous product information"

    __roles__=None

    def __init__(self, name, dict):
        self._d=dict
        self.__name__=name

    def __str__(self): return self.__name__
    def __getitem__(self, name): return self._d[name]
