"""Access control package"""

__version__='$Revision: 1.2 $'[11:-2]

import Globals
from Persistence import Persistent
from Persistence import PersistentMapping
from Acquisition import Implicit
from DocumentTemplate import HTML
from Globals import MessageDialog
from base64 import decodestring
from string import join,strip,split,lower



class SafeDtml(HTML):
    """Lobotomized document template w/no editing"""
    def __init__(self,name='',*args,**kw):
        f=open('%s/lib/python/AccessControl/%s.dtml' % (SOFTWARE_HOME, name))
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

    def __len__(self):
	return 1

    def __str__(self):
	return self._name

    def __repr__(self):
        return self._name

su=SuperUser()


class UserFolder(Implicit, Persistent):
    """ """
    meta_type='User Folder'
    id       ='UserFolder'
    title    ='User Folder'
    icon     ='AccessControl/UserFolder_icon.gif'

    isAUserFolder=1

    manage     =SafeDtml('Generic_manage')
    manage_menu=SafeDtml('Generic_manage_menu')
    manage_main=SafeDtml('UserFolder_manage_main')
    _editForm  =SafeDtml('UserFolder_manage_editForm')
    index_html =manage_main

    manage_options=(
    {'icon':'AccessControl/UserFolder_icon.gif', 'label':'Contents',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'OFS/Help_icon.gif', 'label':'Help',
     'action':'manage_help',   'target':'_new'},
    )

    def _init(self):
	self._data=PersistentMapping()

    def __len__(self):
	return len(self.userNames())

    def parentObject(self):
	try:    return (self.aq_parent,)
	except: return ()

    def userNames(self):
	return self._data.keys()

    def roleNames(self):
	return Globals.Bobobase['roles']

    def validate(self,request,auth,roles=None):
	if lower(auth[:6])!='basic ':
	    return None
	[name,password]=split(decodestring(split(auth)[-1]), ':')
	if (name==su._name) and (password==su._password):
	    return su
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
	if self._data.has_key(name):
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

    def manage_addRole(self,REQUEST,role):
	""" """
	roles=Globals.Bobobase['roles']
	if role not in roles:
	    Globals.Bobobase['roles']=tuple(roles)+(role,)
	return self.manage_main(self, REQUEST)

    def manage_deleteRole(self,REQUEST,role):
	""" """
	roles=Globals.Bobobase['roles']
	if role in roles:
	    roles=list(roles)
	    del roles[roles.index(role)]
	    Globals.Bobobase['roles']=tuple(roles)
	return self.manage_main(self, REQUEST)





def manage_addUserFolder(self,self2,REQUEST):
    """ """
    i=UserFolder()
    i._init()
    self._setObject('UserFolder', i)
    self.__allow_groups__=self.UserFolder
    return self.manage_main(self,REQUEST)
