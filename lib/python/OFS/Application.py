#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  
#
############################################################################## 
__doc__='''Application support


$Id: Application.py,v 1.56 1998/03/23 15:01:22 jeffrey Exp $'''
__version__='$Revision: 1.56 $'[11:-2]


import Globals,Folder,os,regex,sys
import time, rotor, marshal
from string import strip, lower, find, rfind, join
from DateTime import DateTime
from AccessControl.User import UserFolder
from App.ApplicationManager import ApplicationManager
from Persistence import Persistent
from ImageFile import ImageFile

_standard_error_msg='''\
<!--#var standard_html_header-->
<H2>Error: <!--#var error_type-->, <!--#var error_value--></H2>
<!-- <!--#var error_tb--> -->
<!--#var standard_html_footer-->'''

class Application(Folder.Folder):
    title    ='Principia'
    __roles__=['Manager', 'Anonymous']
    __defined_roles__=('Manager','Anonymous','Shared')
    web__form__method='GET'

    class misc_:
	"Miscellaneous product information"
	__roles__=None

    class p_:
	"Shared Principia information"
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
    )

    _reserved_names=('standard_html_header',
		     'standard_html_footer',
		     #'standard_error_message',
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

        self.manage_addDocument('standard_html_header',
	                        'Standard Html Header',
				'<HTML><HEAD><TITLE><!--#var title_or_id-->' \
				'</TITLE></HEAD><BODY BGCOLOR="#FFFFFF">')
        self.manage_addDocument('standard_html_footer',
				'Standard Html Footer',
				'</BODY></HTML>')
	self.manage_addDocument('standard_error_message',
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

    def PrincipiaTime(self):
	"""Utility function to return current date/time"""
	return DateTime()


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

    product_dir=os.path.join(SOFTWARE_HOME,'lib/python/Products')

    install_products()

    __traceback_info__=sys.path
    
    try: app=Bobobase['Application']
    except KeyError:
	app=Application()
	app._init()
	Bobobase['Application']=app
	get_transaction().commit()

    # Backward compatibility
    if not hasattr(app, 'Control_Panel'):
	cpl=ApplicationManager()
        cpl._init()
	app._setObject('Control_Panel', cpl)
	get_transaction().commit()
    if not hasattr(app, 'standard_error_message'):
	app.manage_addDocument('standard_error_message',
			       'Standard Error Message',
			       _standard_error_msg)
	get_transaction().commit()

    return Bobobase





def install_products():
    # Install a list of products into the basic folder class, so
    # that all folders know about top-level objects, aka products

    path_join=os.path.join
    product_dir=path_join(SOFTWARE_HOME,'lib/python/Products')
    isdir=os.path.isdir
    exists=os.path.exists
    DictType=type({})

    from Folder import Folder
    folder_permissions={}
    for permission, names in Folder.__ac_permissions__:
	folder_permissions[permission]=names

    meta_types=list(Folder.dynamic_meta_types)

    product_names=os.listdir(product_dir)
    product_names.sort()

    for product_name in product_names:
	package_dir=path_join(product_dir, product_name)
	if not isdir(package_dir): continue
	if not exists(path_join(package_dir, '__init__.py')):
	    if not exists(path_join(package_dir, '__init__.pyc')):
		continue

	product=getattr(__import__("Products.%s" % product_name), product_name)

	if (pgetattr(product, 'need_license', None, 1) and
	    not lic_check(product_name)):
	    continue

	permissions={}
	for permission, names in pgetattr(product, '__ac_permissions__', ()):
	    for name in names: permissions[name]=permission
	new_permissions={}

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


def lic_check(product_name):
    path_join  =os.path.join
    product_dir=path_join(SOFTWARE_HOME,'lib/python/Products')
    package_dir=path_join(product_dir, product_name)
    bobobase   =Globals.Bobobase
    try: f=open(path_join(package_dir,'%s.lic' % product_name), 'rb')
    except:
	try:
	    product=getattr(__import__("Products.%s" % product_name),
			product_name)
	    for s in pgetattr(product, 'classes', ()):
		p=rfind(s,'.')
		m='Products.%s.%s' % (product_name, s[:p])
		c=s[p+1:]
		__import__(m)
		setattr(sys.modules[m], c, Expired)
	except: pass
	return 0

    dat=f.read()
    f.close()

    dat=lcd(dat)
    if dat is None:
	return 0

    name=dat[0]
    val =dat[1]

    if name != product_name:
	return 0
    if val is None:
	return 1
    else:
	if not bobobase.has_key('_t_'):
	    bobobase['_t_']={}
	t=bobobase['_t_']
	if not t.has_key(product_name):
	    t[product_name]=time.time()
	    bobobase['_t_']=t
	if (t[product_name] + (86400.0 * val)) < time.time():
	    product=getattr(__import__("Products.%s" % product_name),
			    product_name)
	    for s in pgetattr(product, 'classes', ()):
		p=rfind(s,'.')
		m='Products.%s.%s' % (product_name, s[:p])
		c=s[p+1:]
		try: __import__(m)
		except:
		    m=s[:p]
		    __import__(m)
		setattr(sys.modules[m], c, Expired)
	    return 0
	return 1




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

############################################################################## 
#
# $Log: Application.py,v $
# Revision 1.56  1998/03/23 15:01:22  jeffrey
# Added custom error message support
#
# Revision 1.55  1998/03/09 19:37:09  jim
# Check for true need_license before doing license check.
#
# Revision 1.54  1998/03/04 17:13:16  jim
# Added new image to mark objects that were modified in another session
# and are therefore locked.
#
# Revision 1.53  1998/02/25 19:40:47  jim
# Got rid of xxxItems methods.
#
# Revision 1.52  1998/02/23 17:49:01  brian
# Fixed bug that kept rotor from being able to decode licenses with > 7 bit rotor keys
#
# Revision 1.51  1998/02/17 14:23:50  brian
# *** empty log message ***
#
# Revision 1.50  1998/02/14 21:24:31  brian
# Fixed the licensing code to not call get_transaction().commit() during the
# initial request that creates a new bobobase.
#
# Revision 1.49  1998/02/12 23:03:29  brian
# *** empty log message ***
#
# Revision 1.48  1998/02/12 16:24:52  brian
# Fixed eval mode bug ;(
#
# Revision 1.47  1998/02/10 18:25:42  jim
# Re-did the way permissions are handled in install_products, once
# again.
#
# Revision 1.46  1998/02/06 00:25:28  jim
# Fixed bug in handling product permissions.
#
# Revision 1.45  1998/02/05 23:33:46  jim
# Added logic to product installation machinery to handle product
# permissions.
#
# Revision 1.44  1998/02/05 15:17:16  jim
# Added code to tickle cache.
#
# Revision 1.43  1998/01/29 20:52:20  brian
# Fixed up eval support
#
# Revision 1.42  1998/01/28 23:39:02  brian
# Added licensing logic
#
# Revision 1.41  1998/01/22 00:15:00  jim
# Added machinery to handle broken objects
#
# Revision 1.40  1998/01/16 16:02:32  brian
# Fixed bug: install_products only recognized __init__.py files, not .pycs
#
# Revision 1.39  1998/01/15 15:16:45  brian
# Fixed Setup, cleaned up SimpleItem
#
# Revision 1.38  1998/01/13 23:04:54  brian
# Removed __ac_types__
#
# Revision 1.37  1998/01/12 21:31:13  jim
# Made application default Manager, Anonymous
#
# Revision 1.36  1998/01/08 17:40:21  jim
# Modified __class_init__ to use default class init defined in Globals.
#
# Revision 1.35  1998/01/02 17:39:48  jim
# Got rid of old commented line.
#
# Revision 1.34  1997/12/31 16:53:41  brian
# Added security info
#
# Revision 1.33  1997/12/19 19:11:15  jim
# updated icon management strategy
#
# Revision 1.32  1997/12/19 17:04:21  jim
# Make Products a Package.
#
# Revision 1.31  1997/12/19 15:37:34  jim
# Now product __init__s can omit __ foolishness.
# Now products can define misc objects.
#
# Revision 1.30  1997/12/18 18:42:07  jim
# Rearranged things to make fixup "products" work.
#
# Revision 1.29  1997/12/18 17:17:46  jim
# Added rule: only treat a directory in Products as a product if it
# has __init__.py
#
# Revision 1.28  1997/12/18 17:10:40  jim
# Added check for CVS directory.
#
# Revision 1.27  1997/12/18 16:45:38  jeffrey
# changeover to new ImageFile and HTMLFile handling
#
# Revision 1.26  1997/12/17 16:45:26  jim
# initial_products is dead!
#
# Revision 1.25  1997/12/12 21:53:05  brian
# ui support
#
# Revision 1.24  1997/12/12 21:49:41  brian
# ui update
#
# Revision 1.23  1997/12/05 20:33:02  brian
# *** empty log message ***
#
# Revision 1.22  1997/12/05 17:13:48  brian
# New UI
#
# Revision 1.21  1997/11/20 13:40:28  jim
# Added logic to make sure that the top-level user folder gets
# initialized correctly.
#
# Revision 1.20  1997/11/07 17:33:09  jim
# Added code to add Application key to Bobobase if necessary.
#
# Revision 1.19  1997/11/07 17:11:48  brian
# Added role mgmt to Application object
#
# Revision 1.18  1997/11/07 16:09:59  jim
# Added __bobo_traverse__ machinery in support of sessions.
# Updated product installation logic to give OFS special treatment.
#
# Revision 1.17  1997/11/06 22:43:39  brian
# Added global roles to app
#
# Revision 1.16  1997/11/05 15:06:56  paul
# Renamed Redirect to PrincipiaRedirect, leaving Redirect for
# compatibility.  Added PrincipiaTime which returns a DateTime object.
#
# Revision 1.15  1997/10/27 15:21:22  jim
# Fixed bug in assigning role names that caused roles record to be
# rewritten on every start up.
#
# Revision 1.14  1997/09/25 14:04:56  brian
# Added default __roles__ of None, custom roles form
#
# Revision 1.13  1997/09/24 22:16:43  brian
# Style update
#
# Revision 1.12  1997/09/23 10:30:44  jim
# added undo to menu
#
# Revision 1.11  1997/09/19 18:22:29  brian
# Nicified Application
#
# Revision 1.10  1997/09/10 18:42:35  jim
# Added SimpleItem mix-in and new title/id methods.
#
# Revision 1.9  1997/09/09 14:21:07  brian
# Fixed Image editing
#
# Revision 1.8  1997/09/08 23:38:58  brian
# Style mods
#
# Revision 1.7  1997/08/29 18:39:30  brian
# Added role management and fixed a few bugs:
#   o images/manage went nowhere
#   o text on document add form talked about adding images...
#   o added role mgmgt to add forms for Folder,Document,Image
#
# Revision 1.6  1997/08/27 13:30:19  brian
# Changes for UserFolder support:
#   o Added support for role registration to Application.py
#     Products may define a __.role_names in their __init__.py
#     which may be a tuple of role names which will be added to
#     the global list of role names which appears in the role
#     assignment select box when defining/editing a user.
#
#   o Application.Application now has a default __allow_groups__
#     attribute which is a UserFolder with no members defined.
#     This default top-level UF is not visible in the UI, and
#     the user can create a new UF at the top level (in the
#     Application object) at a later time which will simply
#     override the default and be visible in the UI. Since the
#     default UF has no users, an out-of-the-box application's
#     management interfaces will effectively be available to the
#     superuser alone.
#
#   o Removed the __init__ in Folder which created a default ACL.
#     This is no longer needed.
#
#   o Made some minor (but controversial!) style consistency fixes
#     to some of the OFS templates.
#
# Revision 1.5  1997/08/15 22:24:12  jim
# Added Redirect
#
# Revision 1.4  1997/08/08 15:51:27  jim
# Added access control support
#
# Revision 1.3  1997/08/06 18:26:12  jim
# Renamed description->title and name->id and other changes
#
# Revision 1.2  1997/07/28 21:33:08  jim
# Changed top name.
#
# Revision 1.1  1997/07/25 20:03:22  jim
# initial
#
#
