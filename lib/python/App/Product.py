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
"""Product objects
"""
# The new Product model:
# 
#   Products may be defined in the Products folder or by placing directories
#   in lib/python/Products.
# 
#   Products in lib/python/Products may have up to three sources of information:
# 
#       - Static information defined via Python.  This information is
#         described and made available via __init__.py.
# 
#       - Dynamic object data that gets copied into the Bobobase.
#         This is contained in product.dat (which is obfuscated).
# 
#       - Static extensions supporting the dynamic data.  These too
#         are obfuscated.
# 
#   Products may be copied and pasted only within the products folder.
# 
#   If a product is deleted (or cut), it is automatically recreated
#   on restart if there is still a product directory.


import Globals, OFS.Folder, OFS.SimpleItem, os, string, Acquisition, Products
import regex, zlib, Globals, cPickle, marshal, rotor
import ZClasses, ZClasses.ZClass, AccessControl.Owned

from OFS.Folder import Folder
from string import rfind, atoi, find, strip, join
from Factory import Factory
from Permission import PermissionManager
import ZClasses, ZClasses.ZClass
from HelpSys.HelpSys import ProductHelp


class ProductFolder(Folder):
    "Manage a collection of Products"

    id        ='Products'
    name=title='Product Management'
    meta_type ='Product Management'
    icon='p_/ProductFolder_icon'

    all_meta_types={'name': 'Product', 'action': 'manage_addProductForm'},
    meta_types=all_meta_types

    # This prevents subobjects from being owned!
    _owner=AccessControl.Owned.UnownableOwner

    def _product(self, name): return getattr(self, name)

    manage_addProductForm=Globals.DTMLFile('dtml/addProduct',globals())
    def manage_addProduct(self, id, title, REQUEST=None):
        ' '
        i=Product(id, title)
        self._setObject(id,i)
        if REQUEST is not None:
            return self.manage_main(self,REQUEST,update_menu=1)

    def _canCopy(self, op=0):
        return 0

class Product(Folder, PermissionManager):
    """Model a product that can be created through the web.
    """
    meta_type='Product'
    icon='p_/Product_icon'
    version=''
    configurable_objects_=()
    redistributable=0
    import_error_=None
    _isBeingUsedAsAMethod_=1

    def new_version(self,
                    _intending=regex.compile("[.]?[0-9]+$").search, #TS
                    ):
        # Return a new version number based on the existing version.
        v=str(self.version)
        if not v: return '1.0'
        if _intending(v) < 0: return v
        l=rfind(v,'.')
        return v[:l+1]+str(1+atoi(v[l+1:]))            
                    
    
    meta_types=(
        ZClasses.meta_types+PermissionManager.meta_types+
        (
            {
                'name': Factory.meta_type,
                'action': 'manage_addPrincipiaFactoryForm'
                },
            )
        )
    
    manage_addZClassForm=ZClasses.methods['manage_addZClassForm']
    manage_addZClass    =ZClasses.methods['manage_addZClass']
    manage_subclassableClassNames=ZClasses.methods[
        'manage_subclassableClassNames']

    manage_options=(
        Folder.manage_options+
        (
        {'label':'Distribution', 'action':'manage_distributionView',
         'help':('OFSP','Product_Distribution.stx')},
        )
        )

    manage_distributionView=Globals.DTMLFile(
        'dtml/distributionView',globals())

    _properties=Folder._properties+(
        {'id':'version', 'type': 'string'},
        )

    _reserved_names=('Help',)

    manage_addPrincipiaFactoryForm=Globals.DTMLFile(
        'dtml/addFactory',globals())
    def manage_addPrincipiaFactory(
        self, id, title, object_type, initial, permission=None, REQUEST=None):
        ' '
        i=Factory(id, title, object_type, initial, permission)
        self._setObject(id,i)
        factory = self._getOb(id)
        factory.initializePermission()
        if REQUEST is not None:
            return self.manage_main(self,REQUEST,update_menu=1)

    def __init__(self, id, title):
        self.id=id
        self.title=title
        self._setObject('Help', ProductHelp('Help', id))
        
    def Destination(self):
        "Return the destination for factory output"
        return self
    Destination__roles__=None

    def DestinationURL(self):
        "Return the URL for the destination for factory output"
        return self.REQUEST['BASE4']
    DestinationURL__roles__=None

    def manage_distribute(self, version, RESPONSE, configurable_objects=[],
                          redistributable=0):
        "Set the product up to create a distribution and give a link"
        if self.__dict__.has_key('manage_options'):
            raise TypeError, 'This product is <b>not</b> redistributable.'
        self.version=version=strip(version)
        self.configurable_objects_=configurable_objects
        self.redistributable=redistributable
        RESPONSE.redirect('Distributions/%s-%s.tar.gz' % (self.id, version))
        
    def _distribution(self):
        # Return a distribution
        if self.__dict__.has_key('manage_options'):
            raise TypeError, 'This product is <b>not</b> redistributable.'

        id=self.id
        
        import tar
        rot=rotor.newrotor(id+' shshsh')
        ar=tar.tgzarchive("%s-%s" % (id, self.version))
        prefix="lib/python/Products/%s/" % self.id

        # __init__.py
        ar.add(prefix+"__init__.py",
               '''"Product %s"
               ''' % id
               )

        # Extensions
        pp=id+'.'
        lpp=len(pp)
        ed=os.path.join(INSTANCE_HOME,'Extensions')
        if os.path.exists(ed):
            for name in os.listdir(ed):
                suffix=''
                if name[:lpp]==pp:
                    path=os.path.join(ed, name)
                    try:
                        f=open(path)
                        data=f.read()
                        f.close()
                        if name[-3:]=='.py':
                            data=rot.encrypt(zlib.compress(data))
                            suffix='p'
                    except: data=None
                    if data:
                        ar.add("%sExtensions/%s%s" %
                               (prefix,name[lpp:],suffix),
                               data)

        # version.txt
        ar.add(prefix+'version.txt', self.version)

        # product.dat
        f=CompressedOutputFile(rot)
        if self.redistributable:
            # Since it's redistributable, make all objects configurable.
            objectList = self._objects
        else:
            objectList = tuple(filter(
                lambda o, obs=self.configurable_objects_:
                o['id'] in obs,
                self._objects))
        meta={
            '_objects': objectList,
            'redistributable': self.redistributable,
            }
        f.write(cPickle.dumps(meta,1))

        self._p_jar.exportFile(self._p_oid, f)
        ar.add(prefix+'product.dat', f.getdata())

        ar.finish()
        return str(ar)

    class Distributions(Acquisition.Explicit):
        "Product Distributions"

        def __bobo_traverse__(self, REQUEST, name):
            if name[-7:] != '.tar.gz': raise 'Invalid Name', name
            l=find(name,'-')
            id, version = name[:l], name[l+1:-7]
            product=self.aq_parent
            if product.id==id and product.version==version:
                return Distribution(product)

            raise 'Invalid version or product id', name

    Distributions=Distributions()

    manage_traceback=Globals.DTMLFile('dtml/traceback',globals())
    manage_readme=Globals.DTMLFile('dtml/readme',globals())
    def manage_get_product_readme__(self):
        try:
            return open(os.path.join(self.home, 'README.txt')).read()
        except: return ''

    def permissionMappingPossibleValues(self):
        return self.possible_permissions()

    def zclass_product_name(self):
        return self.id

    def getProductHelp(self):
        """
        Returns the ProductHelp object associated
        with the Product.
        """
        if not hasattr(self, 'Help'):
            self._setObject('Help', ProductHelp('Help', self.id))
        return self.Help

class CompressedOutputFile:
    def __init__(self, rot):
        self._c=zlib.compressobj()
        self._r=[]
        self._rot=rot
        rot.encrypt('')

    def write(self, s):
        self._r.append(self._rot.encryptmore(self._c.compress(s)))

    def getdata(self):
        self._r.append(self._rot.encryptmore(self._c.flush()))
        return join(self._r,'')

class CompressedInputFile:
    _done=0
    def __init__(self, f, rot):
        self._c=zlib.decompressobj()
        self._b=''
        if type(rot) is type(''): rot=rotor.newrotor(rot)
        self._rot=rot
        rot.decrypt('')
        self._f=f

    def _next(self):
        if self._done: return
        l=self._f.read(8196)
        if not l:
            l=self._c.flush()
            self._done=1
        else:
            l=self._c.decompress(self._rot.decryptmore(l))
        self._b=self._b+l

    def read(self, l=None):
        if l is None:
            while not self._done: self._next()
            l=len(self._b)
        else:
            while l > len(self._b) and not self._done: self._next()
        r=self._b[:l]
        self._b=self._b[l:]

        return r

    def readline(self):
        l=find(self._b, '\n')
        while l < 0 and not self._done:
            self._next()
            l=find(self._b, '\n')
        if l < 0: l=len(self._b)
        else: l=l+1
        r=self._b[:l]
        self._b=self._b[l:]
        return r

class Distribution:
    "A distribution builder"
    
    def __init__(self, product):
        self._product=product

    def index_html(self, RESPONSE):
        "Return distribution data"
        r=self._product._distribution()
        RESPONSE['content-type']='application/x-gzip'
        return r

def initializeProduct(productp, name, home, app):
    # Initialize a levered product
    products=app.Control_Panel.Products

    if hasattr(productp, '__import_error__'): ie=productp.__import_error__
    else: ie=None

    try: fver=strip(open(home+'/version.txt').read())
    except: fver=''
    old=None
    try:
        if ihasattr(products,name):
            old=getattr(products, name)
            if ihasattr(old,'version') and old.version==fver:
                if hasattr(old, 'import_error_') and \
                   old.import_error_==ie:
                    # Version hasn't changed. Don't reinitialize.
                    return old
    except: pass
    
    disable_distribution = 1
    try:
        f=CompressedInputFile(open(home+'/product.dat','rb'), name+' shshsh')
    except:
        f=fver and (" (%s)" % fver)
        product=Product(name, 'Installed product %s%s' % (name,f))
    else:
        meta=cPickle.Unpickler(f).load()
        product=app._p_jar.importFile(f)
        if meta.get('redistributable', 0):
            disable_distribution = 0
        product._objects=meta['_objects']

    if old is not None:
        app._manage_remove_product_meta_type(product)
        products._delObject(name)
        for id, v in old.objectItems():
            try: product._setObject(id, v)
            except: pass

    products._setObject(name, product)
    #product.__of__(products)._postCopy(products)
    product.icon='p_/InstalledProduct_icon'
    product.version=fver
    product.home=home
    if disable_distribution:
        product.manage_options=Folder.manage_options
        product._distribution=None
        product.manage_distribution=None
    product.thisIsAnInstalledProduct=1

    if ie:
        product.import_error_=ie
        product.title='Broken product %s' % name
        product.icon='p_/BrokenProduct_icon'
        product.manage_options=(
            {'label':'Traceback', 'action':'manage_traceback'},
            )

    if os.path.exists(os.path.join(home, 'README.txt')):
        product.manage_options=product.manage_options+(
            {'label':'README', 'action':'manage_readme'},
            )

    if (os.environ.get('ZEO_CLIENT') and
        not os.environ.get('FORCE_PRODUCT_LOAD')):
        get_transaction().abort()
        return product

    # Give the ZClass fixup code in Application
    Globals.__disk_product_installed__=1
    return product

def ihasattr(o, name):
    return hasattr(o, name) and o.__dict__.has_key(name)
