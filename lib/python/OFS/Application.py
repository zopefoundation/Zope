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

$Id: Application.py,v 1.173 2001/11/26 20:14:24 matt Exp $'''
__version__='$Revision: 1.173 $'[11:-2]

import Globals,Folder,os,sys,App.Product, App.ProductRegistry, misc_
import time, traceback, os, string, Products
from string import strip, lower, find, rfind, join
from DateTime import DateTime
from AccessControl.User import UserFolder
from App.ApplicationManager import ApplicationManager
from webdav.NullResource import NullResource
from FindSupport import FindSupport
from urllib import quote
from StringIO import StringIO
from AccessControl.PermissionRole import PermissionRole
from App.ProductContext import ProductContext
from misc_ import Misc_
import ZDOM
from zLOG import LOG, ERROR, WARNING, INFO
from HelpSys.HelpSys import HelpSys
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

class Application(Globals.ApplicationDefaultPermissions,
                  ZDOM.Root, Folder.Folder,
                  App.ProductRegistry.ProductRegistry, FindSupport):
    """Top-level system object"""
    title    ='Zope'
    #__roles__=['Manager', 'Anonymous']
    __defined_roles__=('Manager','Anonymous','Owner')
    web__form__method='GET'
    isTopLevelPrincipiaApplicationObject=1
    _isBeingUsedAsAMethod_=0

    # Create the help system object
    HelpSys=HelpSys('HelpSys')

    p_=misc_.p_
    misc_=misc_.misc_

    _reserved_names=('Control_Panel',
                     'browser_id_manager',
                     'temp_folder')

    # This class-default __allow_groups__ ensures that the
    # emergency user can still access the system if the top-level
    # UserFolder is deleted. This is necessary to allow people
    # to replace the top-level UserFolder object.
    
    __allow_groups__=UserFolder()

    def title_and_id(self): return self.title
    def title_or_id(self): return self.title

    def __init__(self):
        # Initialize users
        uf=UserFolder()
        self.__allow_groups__=uf
        self._setObject('acl_users', uf)

        # Initialize control panel
        cpl=ApplicationManager()
        cpl._init()
        self._setObject('Control_Panel', cpl)

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

        try: return getattr(self, name)
        except AttributeError: pass
        try: return self[name]
        except KeyError: pass
        method=REQUEST.get('REQUEST_METHOD', 'GET')
        if not method in ('GET', 'POST'):
            return NullResource(self, name, REQUEST).__of__(self)

        # Waaa. unrestrictedTraverse calls us with a fake REQUEST.
        # There is proabably a better fix for this.
        try: REQUEST.RESPONSE.notFoundError("%s\n%s" % (name, method))
        except AttributeError:
            raise KeyError, name

    def PrincipiaTime(self, *args):
        """Utility function to return current date/time"""
        return apply(DateTime, args)
    ZopeTime=PrincipiaTime

    ZopeAttributionButton__roles__=None
    def ZopeAttributionButton(self):
        """Returns an HTML fragment that displays the 'powered by zope'
        button along with a link to the Zope site."""
        return '<a href="http://www.zope.org/Credits" target="_top"><img ' \
               'src="%s/p_/ZopeButton" width="115" height="50" ' \
               'border="0" alt="Powered by Zope" /></a>' % self.REQUEST.BASE1


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

    def absolute_url(self, relative=0):
        """Return an absolute url to the object. Note that the url
        will reflect the acquisition path of the object if the object
        has been acquired."""
        if relative: return ''
        return self.aq_acquire('REQUEST')['BASE1']

    def getPhysicalPath(self):
        '''Returns a path that can be used to access this object again
        later, for example in a copy/paste operation.  Designed to
        be used with getPhysicalRoot().
        '''
        # We're at the base of the path.
        return ('',)

    def getPhysicalRoot(self): return self

    fixupZClassDependencies__roles__=()
    def fixupZClassDependencies(self, rebuild=0):
        # Note that callers should not catch exceptions from this method
        # to ensure that the transaction gets aborted if the registry
        # cannot be rebuilt for some reason. Returns true if any ZClasses
        # were registered as a result of the call or the registry was
        # rebuilt.
        jar=self._p_jar
        result=0

        if rebuild:
            import BTree
            jar.root()['ZGlobals']=BTree.BTree()
            result=1

        zglobals =jar.root()['ZGlobals']
        reg_has_key=zglobals.has_key

        products=self.Control_Panel.Products
        for product in products.objectValues():
            items=list(product.objectItems())
            finished_dict={}
            finished = finished_dict.has_key
            while items:
                name, ob = items.pop()
                base=getattr(ob, 'aq_base', ob)
                if finished(id(base)):
                    continue
                finished_dict[id(base)] = None
                try:
                    # Try to re-register ZClasses if they need it.
                    if hasattr(base,'_register') and hasattr(base,'_zclass_'):
                        class_id=getattr(base._zclass_, '__module__', None)
                        if class_id and not reg_has_key(class_id):
                            ob._register()
                            result=1
                            if not rebuild:
                                LOG('Zope', INFO,
                                    'Registered ZClass: %s' % ob.id
                                    )
                    # Include subobjects.
                    if hasattr(base, 'objectItems'):
                        m = list(ob.objectItems())
                        items.extend(m)
                    # Try to find ZClasses-in-ZClasses.
                    if hasattr(base, 'propertysheets'):
                        ps = ob.propertysheets
                        if (hasattr(ps, 'methods') and
                            hasattr(ps.methods, 'objectItems')):
                            m = list(ps.methods.objectItems())
                            items.extend(m)
                except:
                    LOG('Zope', WARNING,
                        'Broken objects exist in product %s.' % product.id,
                        error=sys.exc_info())

        return result

    checkGlobalRegistry__roles__=()
    def checkGlobalRegistry(self):
        """Check the global (zclass) registry for problems, which can
        be caused by things like disk-based products being deleted.
        Return true if a problem is found"""
        try:
            keys=list(self._p_jar.root()['ZGlobals'].keys())
        except:
            LOG('Zope', ERROR,
                'A problem was found when checking the global product '\
                'registry.  This is probably due to a Product being '\
                'uninstalled or renamed.  The traceback follows.',
                error=sys.exc_info())
            return 1
        return 0

class Expired(Globals.Persistent):
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

def initialize(app):
    # Initialize the application

    # Initialize the cache:
    app.Control_Panel.initialize_cache()

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

    # Ensure that a temp folder exists
    if not hasattr(app, 'temp_folder'):
        from Products.TemporaryFolder.TemporaryFolder import \
             MountedTemporaryFolder
        tf = MountedTemporaryFolder('temp_folder','Temporary Folder')
        app._setObject('temp_folder', tf)
        get_transaction().note('Added temp_folder')
        get_transaction().commit()
        del tf
        
    # Ensure that there is a transient container in the temp folder
    tf = app.temp_folder
    if not hasattr(tf, 'session_data'):
        env_has = os.environ.get
        from Products.Transience.Transience import TransientObjectContainer
        addnotify = env_has('ZSESSION_ADD_NOTIFY', None)
        delnotify = env_has('ZSESSION_DEL_NOTIFY', None)
        default_limit = 1000
        limit = env_has('ZSESSION_OBJECT_LIMIT', default_limit)
        try:
            limit=int(limit)
            if limit != default_limit:
                LOG('Zope Default Object Creation', INFO,
                    ('using ZSESSION_OBJECT_LIMIT-specified max objects '
                     'value of %s' % limit))
        except ValueError:
            LOG('Zope Default Object Creation', WARNING,
                ('Noninteger value %s specified for ZSESSION_OBJECT_LIMIT, '
                 'defaulting to %s' % (limit, default_limit)))
            limit = default_limit
        if addnotify and app.unrestrictedTraverse(addnotify, None) is None:
            LOG('Zope Default Object Creation', WARNING,
                ('failed to use nonexistent "%s" script as '
                 'ZSESSION_ADD_NOTIFY' % addnotify))
            addnotify=None
        elif addnotify:
            LOG('Zope Default Object Creation', INFO,
                'using %s as add notification script' % addnotify)
        if delnotify and app.unrestrictedTraverse(delnotify, None) is None:
            LOG('Zope Default Object Creation', WARNING,
                ('failed to use nonexistent "%s" script as '
                 'ZSESSION_DEL_NOTIFY' % delnotify))
            delnotify=None
        elif delnotify:
            LOG('Zope Default Object Creation', INFO,
                'using %s as delete notification script' % delnotify)

        toc = TransientObjectContainer('session_data',
              'Session Data Container', addNotification = addnotify,
              delNotification = delnotify, limit=limit)
        timeout_spec = env_has('ZSESSION_TIMEOUT_MINS', '')
        if timeout_spec:
            try:
                timeout_spec = int(timeout_spec)
            except ValueError:
                LOG('Zope Default Object Creation', WARNING,
                    ('"%s" is an illegal value for ZSESSION_TIMEOUT_MINS, '
                     'using default timeout instead.' % timeout_spec))
            else:
                LOG('Zope Default Object Creation', INFO,
                    ('using ZSESSION_TIMEOUT_MINS-specified session timeout '
                     'value of %s' % timeout_spec))
                toc = TransientObjectContainer('session_data',
                      'Session Data Container', timeout_mins = timeout_spec,
                      addNotification=addnotify, delNotification = delnotify,
                      limit=limit)
        tf._setObject('session_data', toc)
        tf_reserved = getattr(tf, '_reserved_names', ())
        if 'session_data' not in tf_reserved:
            tf._reserved_names = tf_reserved + ('session_data',)
        get_transaction().note('Added session_data to temp_folder')
        get_transaction().commit()
        del toc
        del addnotify
        del delnotify
        del timeout_spec
        del env_has
        
    del tf

    # Ensure that a browser ID manager exists
    if not hasattr(app, 'browser_id_manager'):
        from Products.Sessions.BrowserIdManager import BrowserIdManager
        bid = BrowserIdManager('browser_id_manager', 'Browser Id Manager')
        app._setObject('browser_id_manager', bid)
        get_transaction().note('Added browser_id_manager')
        get_transaction().commit()
        del bid

    # Ensure that a session data manager exists
    if not hasattr(app, 'session_data_manager'):
        from Products.Sessions.SessionDataManager import SessionDataManager
        sdm = SessionDataManager('session_data_manager',
            title='Session Data Manager',
            path='/temp_folder/session_data',
            requestName='SESSION')
        app._setObject('session_data_manager', sdm)
        get_transaction().note('Added session_data_manager')
        get_transaction().commit()
        del sdm

    # Ensure that there's an Examples folder with examples.
    # However, make sure that if the examples have been added already
    # and then deleted that we don't add them again.
    if not hasattr(app, 'Examples') and not \
       hasattr(app, '_Zope25_examples_have_been_added'):
        examples_path = os.path.join(Globals.data_dir, 'Examples.zexp')
        if os.path.isfile(examples_path):
            app._importObjectFromFile(examples_path, verify=0)
            app._Zope25_examples_have_been_added=1
            get_transaction().note('Added Examples folder')
            get_transaction().commit()
        else:
            LOG('Zope Default Object Creation', INFO,
                '%s examples import file could not be found.' % examples_path)

    # b/c: Ensure that Owner role exists.
    if hasattr(app, '__ac_roles__') and not ('Owner' in app.__ac_roles__):
        app.__ac_roles__=app.__ac_roles__ + ('Owner',)
        get_transaction().note('Added Owner role')
        get_transaction().commit()

    # ensure the Authenticated role exists.
    if hasattr(app, '__ac_roles__'):
        if not 'Authenticated' in app.__ac_roles__:
            app.__ac_roles__=app.__ac_roles__ + ('Authenticated',)
            get_transaction().note('Added Authenticated role')
            get_transaction().commit()

    # Make sure we have Globals
    root=app._p_jar.root()
    if not root.has_key('ZGlobals'):
        import BTree
        app._p_jar.root()['ZGlobals']=BTree.BTree()
        get_transaction().note('Added Globals')
        get_transaction().commit()

    # Install the initial user.
    if hasattr(app, 'acl_users'):
        users = app.acl_users
        if hasattr(users, '_createInitialUser'):
            app.acl_users._createInitialUser()
            get_transaction().note('Created initial user')
            get_transaction().commit()

    install_products(app)
    install_standards(app)

    # Note that the code from here on only runs if we are not a ZEO
    # client, or if we are a ZEO client and we've specified by way
    # of env variable that we want to force products to load.
    if (os.environ.get('ZEO_CLIENT') and
        not os.environ.get('FORCE_PRODUCT_LOAD')):
        return

    # Check for dangling pointers (broken zclass dependencies) in the
    # global class registry. If found, rebuild the registry. Note that
    # if the check finds problems but fails to successfully rebuild the 
    # registry we abort the transaction so that we don't leave it in an
    # indeterminate state.

    did_fixups=0
    bad_things=0
    try:
        if app.checkGlobalRegistry():
            LOG('Zope', INFO,
                'Beginning attempt to rebuild the global ZClass registry.')
            app.fixupZClassDependencies(rebuild=1)
            did_fixups=1
            LOG('Zope', INFO,
                'The global ZClass registry has successfully been rebuilt.')
            get_transaction().note('Rebuilt global product registry')
            get_transaction().commit()
    except:
        bad_things=1
        LOG('Zope', ERROR, 'The attempt to rebuild the registry failed.',
            error=sys.exc_info())
        get_transaction().abort()

    # Now we need to see if any (disk-based) products were installed
    # during intialization. If so (and the registry has no errors),
    # there may still be zclasses dependent on a base class in the
    # newly installed product that were previously broken and need to
    # be fixed up. If any really Bad Things happened (dangling pointers
    # were found in the registry but it couldn't be rebuilt), we don't
    # try to do anything to avoid making the problem worse.
    if (not did_fixups) and (not bad_things):

        # App.Product.initializeProduct will set this if a disk-based
        # product was added or updated and we are not a ZEO client.
        if getattr(Globals, '__disk_product_installed__', 0):
            try:
                LOG('Zope', INFO, 'New disk product detected, determining '\
                    'if we need to fix up any ZClasses.')
                if app.fixupZClassDependencies():
                    LOG('Zope', INFO, 'Repaired broken ZClass dependencies.')
                    get_transaction().commit()
            except:
                LOG('Zope', ERROR,
                    'Attempt to fixup ZClass dependencies after detecting ' \
                    'an updated disk-based product failed.',
                    error=sys.exc_info())
                get_transaction().abort()

def get_products():
    """ Return a list of tuples in the form:
    [(priority, dir_name, index, base_dir), ...] for each Product directory
    found, sort before returning """
    products = []
    i = 0
    for product_dir in Products.__path__:
        product_names=os.listdir(product_dir)
        for name in product_names:
            priority = (name != 'PluginIndexes') # import PluginIndexes 1st
            # i is used as sort ordering in case a conflict exists
            # between Product names.  Products will be found as
            # per the ordering of Products.__path__
            products.append((priority, name, i, product_dir))
        i = i + 1
    products.sort()
    return products

def import_products():
    # Try to import each product, checking for and catching errors.
    done={}

    products = get_products()

    for priority, product_name, index, product_dir in products:
        if done.has_key(product_name):
            LOG('OFS.Application', WARNING, 'Duplicate Product name',
                'After loading Product %s from %s,\n'
                'I skipped the one in %s.\n' % (
                `product_name`, `done[product_name]`, `product_dir`) )
            continue
        done[product_name]=product_dir
        import_product(product_dir, product_name)

def import_product(product_dir, product_name, raise_exc=0, log_exc=1):
    path_join=os.path.join
    isdir=os.path.isdir
    exists=os.path.exists
    _st=type('')
    global_dict=globals()
    silly=('__doc__',)
    modules=sys.modules
    have_module=modules.has_key

    if 1:  # Preserve indentation for diff :-)
        try:
            package_dir=path_join(product_dir, product_name)
            if not isdir(package_dir): return
            if not exists(path_join(package_dir, '__init__.py')):
                if not exists(path_join(package_dir, '__init__.pyc')):
                    if not exists(path_join(package_dir, '__init__.pyo')):
                        return

            pname="Products.%s" % product_name
            try:
                product=__import__(pname, global_dict, global_dict, silly)
                if hasattr(product, '__module_aliases__'):
                    for k, v in product.__module_aliases__:
                        if not have_module(k):
                            if type(v) is _st and have_module(v): v=modules[v]
                            modules[k]=v
            except:
                exc = sys.exc_info()
                if log_exc:
                    LOG('Zope', ERROR, 'Could not import %s' % pname,
                        error=exc)
                f=StringIO()
                traceback.print_exc(100,f)
                f=f.getvalue()
                try: modules[pname].__import_error__=f
                except: pass
                if raise_exc:
                    raise exc[0], exc[1], exc[2]
        finally:
            exc = None


def install_products(app):
    # Install a list of products into the basic folder class, so
    # that all folders know about top-level objects, aka products

    folder_permissions = get_folder_permissions()
    meta_types=[]
    done={}

    get_transaction().note('Prior to product installs')
    get_transaction().commit()

    products = get_products()

    for priority, product_name, index, product_dir in products:
        # For each product, we will import it and try to call the
        # intialize() method in the product __init__ module. If
        # the method doesnt exist, we put the old-style information
        # together and do a default initialization.
        if done.has_key(product_name):
            continue
        done[product_name]=1
        install_product(app, product_dir, product_name, meta_types,
                        folder_permissions)

    Products.meta_types=Products.meta_types+tuple(meta_types)
    Globals.default__class_init__(Folder.Folder)


def get_folder_permissions():
    folder_permissions={}
    for p in Folder.Folder.__ac_permissions__:
        permission, names = p[:2]
        folder_permissions[permission]=names
    return folder_permissions


def install_product(app, product_dir, product_name, meta_types,
                    folder_permissions, raise_exc=0, log_exc=1):

    path_join=os.path.join
    isdir=os.path.isdir
    exists=os.path.exists
    DictType=type({})
    global_dict=globals()
    silly=('__doc__',)

    if 1:  # Preserve indentation for diff :-)
            package_dir=path_join(product_dir, product_name)
            __traceback_info__=product_name
            if not isdir(package_dir): return
            if not exists(path_join(package_dir, '__init__.py')):
                if not exists(path_join(package_dir, '__init__.pyc')):
                    if not exists(path_join(package_dir, '__init__.pyo')):
                        return
            try:
                product=__import__("Products.%s" % product_name,
                                   global_dict, global_dict, silly)

                # Install items into the misc_ namespace, used by products
                # and the framework itself to store common static resources
                # like icon images.
                misc_=pgetattr(product, 'misc_', {})
                if misc_:
                    if type(misc_) is DictType:
                        misc_=Misc_(product_name, misc_)
                    Application.misc_.__dict__[product_name]=misc_

                # Here we create a ProductContext object which contains
                # information about the product and provides an interface
                # for registering things like classes and help topics that
                # should be associated with that product. Products are
                # expected to implement a method named 'initialize' in
                # their __init__.py that takes the ProductContext as an
                # argument.
                productObject=App.Product.initializeProduct(
                    product, product_name, package_dir, app)
                context=ProductContext(productObject, app, product)

                # Look for an 'initialize' method in the product. If it does
                # not exist, then this is an old product that has never been
                # updated. In that case, we will analyze the product and
                # build up enough information to do initialization manually.
                initmethod=pgetattr(product, 'initialize', None)
                if initmethod is not None:
                    initmethod(context)

                # Support old-style product metadata. Older products may
                # define attributes to name their permissions, meta_types,
                # constructors, etc.
                permissions={}
                new_permissions={}
                for p in pgetattr(product, '__ac_permissions__', ()):
                    permission, names, default = (
                        tuple(p)+('Manager',))[:3]
                    if names:
                        for name in names:
                            permissions[name]=permission
                    elif not folder_permissions.has_key(permission):
                        new_permissions[permission]=()

                for meta_type in pgetattr(product, 'meta_types', ()):
                    # Modern product initialization via a ProductContext
                    # adds 'product' and 'permission' keys to the meta_type
                    # mapping. We have to add these here for old products.
                    pname=permissions.get(meta_type['action'], None)
                    if pname is not None:
                        meta_type['permission']=pname
                    meta_type['product']=productObject.id
                    meta_type['visibility'] = 'Global'
                    meta_types.append(meta_type)

                for name,method in pgetattr(
                    product, 'methods', {}).items():
                    if not hasattr(Folder.Folder, name):
                        setattr(Folder.Folder, name, method)
                        if name[-9:]!='__roles__': # not Just setting roles
                            if (permissions.has_key(name) and
                                not folder_permissions.has_key(
                                    permissions[name])):
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
                    Folder.Folder.__dict__['__ac_permissions__']=tuple(
                        list(Folder.Folder.__ac_permissions__)+new_permissions)

                if (os.environ.get('ZEO_CLIENT') and
                    not os.environ.get('FORCE_PRODUCT_LOAD')):
                    # we don't want to install products from clients
                    # (unless FORCE_PRODUCT_LOAD is defined).
                    get_transaction().abort()
                else:
                    get_transaction().note('Installed product '+product_name)
                    get_transaction().commit()

            except:
                if log_exc:
                    LOG('Zope',ERROR,'Couldn\'t install %s' % product_name,
                        error=sys.exc_info())
                get_transaction().abort()
                if raise_exc:
                    raise

def install_standards(app):
    # Install the replaceable standard objects
    std_dir = os.path.join(Globals.package_home(globals()), 'standard')
    wrote = 0
    for fn in os.listdir(std_dir):
        base, ext = os.path.splitext(fn)
        if ext == '.dtml':
            ob = Globals.DTMLFile(base, std_dir)
            fn = base
            if hasattr(app, fn):
                continue
            app.manage_addProduct['OFSP'].manage_addDTMLMethod(
                id=fn, file=open(ob.raw))
        elif ext in ('.pt', '.zpt'):
            ob = PageTemplateFile(fn, std_dir, __name__=fn)
            if hasattr(app, fn):
                continue
            app.manage_addProduct['PageTemplates'].manage_addPageTemplate(
                id=fn, title='', text=open(ob.filename))
        else:
            continue
        wrote = 1
        ob.__replaceable__ = Globals.REPLACEABLE
        setattr(Application, fn, ob)
    if wrote:
        get_transaction().note('Installed standard objects')
        get_transaction().commit()

def reinstall_product(app, product_name):
    folder_permissions = get_folder_permissions()
    meta_types=[]

    get_transaction().note('Prior to product reinstall')
    get_transaction().commit()

    for product_dir in Products.__path__:
        product_names=os.listdir(product_dir)
        product_names.sort()
        if product_name in product_names:
            removeProductMetaTypes(product_name)
            install_product(app, product_dir, product_name, meta_types,
                            folder_permissions, raise_exc=1, log_exc=0)
            break

    Products.meta_types=Products.meta_types+tuple(meta_types)
    Globals.default__class_init__(Folder.Folder)


def reimport_product(product_name):
    for product_dir in Products.__path__:
        product_names=os.listdir(product_dir)
        product_names.sort()
        if product_name in product_names:
            import_product(product_dir, product_name,
                           raise_exc=1, log_exc=0)
            break


def removeProductMetaTypes(pid):
    '''
    Unregisters the meta types registered by a product.
    '''
    meta_types = Products.meta_types
    new_mts = []
    changed = 0
    for meta_type in meta_types:
        if meta_type.get('product', None) == pid:
            # Remove this meta type.
            changed = 1
        else:
            new_mts.append(meta_type)
    if changed:
        Products.meta_types = tuple(new_mts)


def pgetattr(product, name, default=install_products, __init__=0):
    if not __init__ and hasattr(product, name): return getattr(product, name)
    if hasattr(product, '__init__'):
        product=product.__init__
        if hasattr(product, name): return getattr(product, name)

    if default is not install_products: return default

    raise AttributeError, name
