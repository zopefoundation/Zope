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
__doc__='''Application support


$Id: Application.py,v 1.94 1999/03/25 15:29:55 jim Exp $'''
__version__='$Revision: 1.94 $'[11:-2]


import Globals,Folder,os,regex,sys,App.Product, App.ProductRegistry
import time, traceback, os, string
from string import strip, lower, find, rfind, join
from DateTime import DateTime
from AccessControl.User import UserFolder
from HelpSys.HelpSys import HelpSys
from App.ApplicationManager import ApplicationManager
from Globals import Persistent
from FindSupport import FindSupport
from ImageFile import ImageFile
from urllib import quote
from cStringIO import StringIO


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
    _isBeingUsedAsAMethod_=0

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
        dtmldoc=doc=ImageFile('www/dtmldoc.gif', globals())
        dtmlmethod =ImageFile('www/dtmlmethod.gif', globals())
        
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
        BrokenProduct_icon=ImageFile('App/www/brokenProduct.gif')
        Product_icon=ImageFile('App/www/product.gif')
        Factory_icon=ImageFile('App/www/factory.gif')
        ProductFolder_icon=ImageFile('App/www/productFolder.gif')
        PyPoweredSmall_Gif=ImageFile('App/www/PythonPoweredSmall.gif')

        ZopeButton=ImageFile('App/www/zope_button.gif')

        #up=ImageFile('www/UpFolder_icon.gif', globals())
        #help=ImageFile('www/Help_icon.gif', globals())

    manage_options=(
    {'icon':'OFS/Folder_icon.gif', 'label':'Contents',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'OFS/Properties_icon.gif', 'label':'Properties',
     'action':'manage_propertiesForm',   'target':'manage_main'},
    {'label':'Import/Export', 'action':'manage_importExportForm',
     'target':'manage_main'},
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

    def __class_init__(self): Globals.default__class_init__(self)

    def PrincipiaRedirect(self,destination,URL1):
        """Utility function to allow user-controlled redirects"""
        if find(destination,'//') >= 0: raise 'Redirect', destination
        raise 'Redirect', ("%s/%s" % (URL1, destination))
    Redirect=ZopeRedirect=PrincipiaRedirect

    def __bobo_traverse__(self, REQUEST, name=None):
        if name is None and REQUEST.has_key(Globals.VersionNameName):
            pd=Globals.VersionBase[REQUEST[Globals.VersionNameName]]
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
    ZopeTime=PrincipiaTime

    def ZopeAttributionButton(self):
        """Returns an HTML fragment that displays the 'powered by zope'
        button along with a link to the Zope site. Use this method to
        easily comply with the Zope attribute requirement."""
        return '<a href="http://www.zope.org/Credits"><img ' \
               'src="%s/p_/ZopeButton" width="60" height="82" ' \
               'border="0" alt="Powered by Zope"></a>' % self.REQUEST.BASE1


    def DELETE(self, REQUEST, RESPONSE):
        """Delete a resource object."""
        self.dav__init(REQUEST, RESPONSE)
        raise 'Forbidden', 'This resource cannot be deleted.'

    def MOVE(self, REQUEST, RESPONSE):
        """Move a resource to a new location."""
        self.dav__init(REQUEST, RESPONSE)
        raise 'Forbidden', 'This resource cannot be moved.'
    
    test_url___allow_groups__=None
    test_url=ZopeAttributionButton





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

    import_products()

    revision=read_only=None

    if os.environ.has_key('ZOPE_READ_ONLY'):
        read_only=1
        try: revision=DateTime(os.environ['ZOPE_READ_ONLY']).timeTime()
        except: pass
        
    Bobobase=Globals.Bobobase=Globals.PickleDictionary(
        Globals.BobobaseName, read_only=read_only, revision=revision)

    product_dir=os.path.join(SOFTWARE_HOME,'Products')

    __traceback_info__=sys.path
    
    try: app=Bobobase['Application']
    except KeyError:
        app=Application()
        app._init()
        Bobobase['Application']=app
        get_transaction().note('created Application object')
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
        get_transaction().note('Added Control_Panel')
        get_transaction().commit()

    # b/c: Ensure that a ProductFolder exists.
    if not hasattr(app.Control_Panel.aq_base, 'Products'):
        app.Control_Panel.Products=App.Product.ProductFolder()
        get_transaction().note('Added Control_Panel.Products')
        get_transaction().commit()

    # b/c: Ensure that std err msg exists.
    if not hasattr(app, 'standard_error_message'):
        import Document
        Document.manage_addDocument(
            app,
            'standard_error_message',
            'Standard Error Message',
            _standard_error_msg)
        get_transaction().note('Added standard_error_message')
        get_transaction().commit()

    install_products(app)
    get_transaction().note('Product installations')
    get_transaction().commit()

    return Bobobase

def import_products(_st=type('')):
    # Try to import each product, checking for and catching errors.
    path_join=os.path.join
    product_dir=path_join(SOFTWARE_HOME,'Products')
    isdir=os.path.isdir
    exists=os.path.exists
    DictType=type({})

    product_names=os.listdir(product_dir)
    product_names.sort()
    global_dict=globals()
    silly=('__doc__',)
    modules=sys.modules
    have_module=modules.has_key

    for product_name in product_names:
        package_dir=path_join(product_dir, product_name)
        if not isdir(package_dir): continue
        if not exists(path_join(package_dir, '__init__.py')):
            if not exists(path_join(package_dir, '__init__.pyc')):
                continue

        pname="Products.%s" % product_name
        try:
            product=__import__(pname, global_dict, global_dict, silly)
            if hasattr(product, '__module_aliases__'):
                for k, v in product.__module_aliases__:
                    if not have_module(k):
                        if type(v) is _st and have_module(v): v=modules[v]
                        modules[k]=v
        except:
            f=StringIO()
            traceback.print_exc(100,f)
            f=f.getvalue()
            try: modules[pname].__import_error__=f
            except: pass

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
        __traceback_info__=product_name
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
        App.Product.initializeProduct(product, product_name, package_dir, app)

        get_transaction().note('Installed product '+product_name)
        get_transaction().commit()

    Folder.dynamic_meta_types=tuple(meta_types)

    Globals.default__class_init__(Folder)


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
