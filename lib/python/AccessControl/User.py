"""Access control package"""

__version__='$Revision: 1.24 $'[11:-2]

import Globals
from Persistence import Persistent
from PersistentMapping import PersistentMapping
from App.Management import Management
from OFS.SimpleItem import Item
from Acquisition import Implicit
from DocumentTemplate import HTML
from Globals import MessageDialog
from base64 import decodestring
from string import join,strip,split,lower
from ImageFile import ImageFile


class SafeDtml(HTML):
    """Lobotomized document template"""
    def __init__(self,name='',*args,**kw):
        f=open('%s/lib/python/%s.dtml' % (SOFTWARE_HOME, name))
        s=f.read()
        f.close()
        args=(self,s,)+args
	kw['SOFTWARE_URL']=SOFTWARE_URL
	apply(HTML.__init__,args,kw)
    manage             =None
    manage_editDocument=None
    manage_editForm    =None
    manage_edit        =None





class User(Implicit, Persistent):
    def __init__(self,name=None,password=None,roles=[]):
	if name is not None:
	    self._name    =name
	    self._password=password
	    self._roles   =roles

    def hasRole(self,roles=None):
	if roles is None:
	    return 1
	for role in roles:
	    if role in self._roles:
		return 1
	return 0

    def __len__(self):
	return 1

    def __str__(self):
	return self._name

    def __repr__(self):
        return self._name


class SuperUser:
    def __init__(self):
	try:
	    f=open('%s/access' % CUSTOMER_HOME, 'r')
	    d=split(strip(f.readline()),':')
	    f.close()
	    self._name    =d[0]
	    self._password=d[1]
	    self._roles   =('manage',)
	except:
	    self._name    ='superuser'
	    self._password='123'
	    self._roles   =('manage',)

    def hasRole(self,roles=None):
	return 1

    def __len__(self):
	return 1

    def __str__(self):
	return self._name

    def __repr__(self):
        return self._name

super=SuperUser()



class UserFolder(Persistent, Item, Implicit, Management):
    """ """
    meta_type='User Folder'
    id       ='acl_users'
    title    ='User Folder'
    icon='p_/UserFolder'

    isPrincipiaFolderish=1
    isAUserFolder=1

    manage_main=Globals.HTMLFile('UserFolder_manage_main', globals())
    _editForm  =Globals.HTMLFile('UserFolder_manage_editForm', globals())
    manage=manage_main
    #index_html =manage_main

    manage_options=(
    {'icon':'AccessControl/UserFolder_icon.gif', 'label':'Contents',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'App/undo_icon.gif', 'label':'Undo',
     'action':'manage_UndoForm', 'target':'manage_main'},
    )

    def _init(self):
	self._data=PersistentMapping()

    def __len__(self):
	return len(self.userNames())

    def parentObject(self):
	try:    return (self.aq_parent,)
	except: return ()

    def _isTop(self):
	try:    t=self.aq_parent.aq_parent.acl_users
	except: return 1
	return 0

    def userNames(self):
	try: return self._data.keys()
	except AttributeError:
	    self._init()
	    return ()

    def roleNames(self):
	return self.validRoles()

    def validate(self,request,auth,roles=None):
	if lower(auth[:6])!='basic ':
	    return None
	[name,password]=split(decodestring(split(auth)[-1]), ':')

	if self._isTop() and (name==super._name) and \
	   (password==super._password):
	    return super

	try:    user=self._data[name]
	except: return None
	if password!=user._password:
	    return None
	if roles is None:
	    return user
	for role in roles:
	    if role in user._roles:
		return user
	return None

    def manage_addUser(self,REQUEST,name,password,confirm,roles=[]):
        """ """
	if self._data.has_key(name) or (name==super._name):
            return MessageDialog(title='Illegal value', 
                   message='An item with the specified name already exists',
                   action='%s/manage' % REQUEST['PARENT_URL'])

	if password!=confirm:
            return MessageDialog(title='Illegal value', 
                   message='Password and confirmation do not match',
                   action='%s/manage' % REQUEST['PARENT_URL'])
        self._data[name]=User(name,password,roles)
        return self.manage_main(self, REQUEST)

    def manage_editForm(self,REQUEST,name):
        """ """
	try:    user=self._data[name]
	except: return MessageDialog(title='Illegal value',
                message='The specified item does not exist',
                action='%s/manage_main' % REQUEST['PARENT_URL'])
	name    =user._name
	pw      =user._password
	rolelist=map(lambda k, s=user._roles:
		     k in s and ('<OPTION VALUE="%s" SELECTED>%s' % (k,k)) \
		     or  ('<OPTION VALUE="%s">%s' % (k,k)), self.roleNames())
	return self._editForm(self,REQUEST,name=name,pw=pw,rolelist=rolelist)

    def manage_editUser(self,REQUEST,name,password,confirm,roles=[]):
        """ """
	try:    user=self._data[name]
	except: return MessageDialog(title='Illegal value',
                message='The specified item does not exist',
                action='%s/manage_main' % REQUEST['PARENT_URL'])
	if password!=confirm:
            return MessageDialog(title='Illegal value', 
                   message='Password and confirmation do not match',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])
	user._password=password
	user._roles   =roles
        return self.manage_main(self, REQUEST)

    def manage_deleteUser(self,REQUEST,names=[]):
        """ """
	if 0 in map(self._data.has_key, names):
            return MessageDialog(title='Illegal value',
                   message='One or more items specified do not exist',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])
	for n in names:
            del self._data[n]
        return self.manage_main(self, REQUEST)

    def _getCopy(self, container):
	try:    obj=container.aq_self
	except: obj=container
	if hasattr(obj,'acl_users'):
	    raise ('Copy Error',
		   '<EM>This object already contains a UserFolder</EM>')
	return loads(dumps(self))

    def _postCopy(self, container):
	container.__allow_groups__=container.acl_users

    def _setId(self, clip_id):
	if clip_id != self.id:
	     raise ('Copy Error',
		    '<EM>Cannot change the id of a UserFolder</EM>')




class UserFolderHandler:
    """ """
    meta_types_=({'name':'User Folder', 'action':'manage_addUserFolder'},)

    def manage_addUserFolder(self,dtself,REQUEST,**ignored):
        """ """
        i=UserFolder()
        i._init()
	try:    self._setObject('acl_users', i)
	except: return MessageDialog(title='Item Exists',
                       message='This object already contains a User Folder',
                       action='%s/manage_main' % REQUEST['PARENT_URL'])
        self.__allow_groups__=self.acl_users
        return self.manage_main(self,REQUEST)

    def UserFolderIds(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='User Folder':
		t.append(i['id'])
	return t

    def UserFolderValues(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='User Folder':
		t.append(getattr(self,i['id']))
	return t

    def UserFolderItems(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='User Folder':
		n=i['id']
		t.append((n,getattr(self,n)))
	return t




# $Log: User.py,v $
# Revision 1.24  1997/12/19 19:03:54  jim
# updated icon management strategy
#
# Revision 1.23  1997/12/18 21:12:47  jeffrey
# more ImageFile tweaks
#
# Revision 1.22  1997/12/18 16:45:28  jeffrey
# changeover to new ImageFile and HTMLFile handling
#
# Revision 1.21  1997/12/18 13:34:04  jim
# Changed PersistentMapping import
#
# Revision 1.20  1997/12/05 17:10:10  brian
# New UI
#
# Revision 1.19  1997/11/20 13:39:54  jim
# Added logic to check for a broken user folder.
#
# Revision 1.18  1997/11/11 22:38:26  brian
# Added copy logic to UF
#
# Revision 1.17  1997/11/07 20:57:41  jim
# Made manage_addUserFolder accept and ignore keyword arguments to be
# compatible with the new addObject protocol.
#
# Revision 1.16  1997/11/07 17:33:57  jim
# Renamed meta_types to meta_types_ for new OFS-as-product change.
#
# Revision 1.15  1997/11/07 17:09:31  brian
# Fixed validRoles
#
# Revision 1.14  1997/10/23 17:35:45  brian
# Added hasRole method to User objects
#
# Revision 1.13  1997/09/19 17:52:04  brian
# Changed UFs so that only the top UF validates god.
#
# Revision 1.12  1997/09/17 14:59:42  brian
# *** empty log message ***
#
# Revision 1.11  1997/09/15 15:00:24  brian
# Added SimpleItem support
#
# Revision 1.10  1997/09/08 23:01:33  brian
# Style mods
#
# Revision 1.9  1997/09/04 20:35:36  brian
# Fixed truth test bug in UserFolder
#
# Revision 1.8  1997/08/29 18:34:54  brian
# Added basic role management to package.
#
# Revision 1.7  1997/08/27 19:49:48  brian
# Added forgotten dtml
#
# Revision 1.6  1997/08/27 13:44:00  brian
# Added a nicer dialog to return if users try to create more than one
# UserFolder in an object.
#
# Revision 1.5  1997/08/27 13:31:28  brian
# Fixed a name boo-boo
#
# Revision 1.4  1997/08/27 13:16:27  brian
# Added cvs log!
#
