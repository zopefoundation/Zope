"""Access control objects"""

__version__='$Revision: 1.1 $'[11:-2]


from Persistence import Persistent
from DocumentTemplate import HTML
from Globals import MessageDialog
from Acquisition import Acquirer
from string import join, strip, split



class SafeDtml(HTML):
    """Lobotomized document template w/no editing"""

    def __init__(self,name='',*args,**kw):
        f=open('%s/lib/python/AccessControl/%s.dtml' % (SOFTWARE_HOME, name))
        s=f.read()
        f.close()
        args=(self,s,)+args
	apply(HTML.__init__,args,kw)

    manage             =None
    manage_editDocument=None
    manage_editForm    =None
    manage_edit        =None






class ACL(Persistent, Acquirer):
    """An object which stores and provides a user 
       interface to access control information"""

    def __init__(self, groups=[]):
        self._data={}
	for g in groups:
            self._data[g]={}

    id         ='AccessControl'
    title      ='Access Control'
    icon       ='AccessControl/AccessControl_icon.gif'

    _groupsForm=SafeDtml('groupsForm')
    _groupForm =SafeDtml('groupForm')
    _memberForm=SafeDtml('memberForm')

    manage=manage_main=_groupsForm

    def debug(self):
        """ """
        return '<html><XMP>%s</XMP></html>' % `self`

    def __len__(self): return len(self._data)

    def has_key(self,k):
        return self._data.has_key(k)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __getitem__(self,k):
        return self._data[k]

    def __setitem__(self,k, v):
        self._data[k]=v
        self.__changed__(1)

    def __delitem__(self,k):
        del self._data[k]
        self.__changed__(1)

    def groupNames(self):
        return self._data.keys()

    def manage_addGroup(self,REQUEST,name=''):
        """Add group"""
	if not name:
            return MessageDialog(title='Illegal value', 
                   message='An illegal value was specified',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

        if self._data.has_key(name):
            return MessageDialog(title='Illegal value',
                   message='An item with the specified name already exists',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

        self._data[name]={}
        self.__changed__(1)
        return self._groupsForm(self,REQUEST)


    def manage_groupForm(self,REQUEST,name=''):
        """Edit group"""
	if not (name):
            return MessageDialog(title='Illegal value', 
                   message='An illegal value was specified',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

        if not self._data.has_key(name):
            return MessageDialog(title='Illegal value',
                   message='The specified item does not exist',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

	return self._groupForm(self,REQUEST,groupName=name,
                               memberNames=self._data[name].keys())

    def manage_deleteGroup(self,REQUEST,names=[]):
        """Delete group"""
	if not names:
            return MessageDialog(title='Illegal value', 
                   message='An illegal value was specified',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

	if type(names)==type('s'): names=[names]

        f=self._data.has_key
	if 0 in map(f, names):
            return MessageDialog(title='Illegal value',
                   message='The specified item does not exist',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

	for n in names:
            del self._data[n]
        self.__changed__(1)
        return self._groupsForm(self,REQUEST)


    def manage_addMember(self,REQUEST,group='',name='',password='',confirm=''):
        """Add a member"""
	if not (group and name and password and confirm):
            return MessageDialog(title='Illegal value', 
                   message='An illegal value was specified',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

        if not self._data.has_key(group):
            return MessageDialog(title='Illegal value',
                   message='The specified item does not exist',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

	if self._data[group].has_key(name):
            return MessageDialog(title='Illegal value', 
                   message='An item with the specified name already exists',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

	if password != confirm:
            return MessageDialog(title='Illegal value', 
                   message='Password and confirmation do not match',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

        self._data[group][name]=password
        self.__changed__(1)
	return self._groupForm(self,REQUEST,groupName=group,
                               memberNames=self._data[group].keys())


    def manage_memberForm(self,REQUEST,group='',name=''):
        """Edit member"""
	if not (group and name):
            return MessageDialog(title='Illegal value', 
                   message='An illegal value was specified',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

        if not self._data.has_key(group):
            return MessageDialog(title='Illegal value',
                   message='The specified item does not exist',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

        if not self._data[group].has_key(name):
            return MessageDialog(title='Illegal value',
                   message='The specified item does not exist',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

	g,n,p=group,name,self._data[group][name]
        return self._memberForm(self,REQUEST,groupName=g,memberName=n,
                                memberPassword=p)


    def manage_editMember(self,REQUEST,group='',name='',password='',
                          confirm=''):
        """Add a member"""
	if not (group and name and password and confirm):
            return MessageDialog(title='Illegal value', 
                   message='An illegal value was specified',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

        if not self._data.has_key(group):
            return MessageDialog(title='Illegal value',
                   message='The specified item does not exist',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

	if not self._data[group].has_key(name):
            return MessageDialog(title='Illegal value',
                   message='The specified item does not exist',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

	if password != confirm:
            return MessageDialog(title='Illegal value', 
                   message='Password and confirmation do not match',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

        self._data[group][name]=password
        self.__changed__(1)
	return self._groupForm(self,REQUEST,groupName=group,
                               memberNames=self._data[group].keys())


    def manage_deleteMember(self,REQUEST,group='',names=[]):
        """Delete members"""
	if not (group and names):
            return MessageDialog(title='Illegal value', 
                   message='An illegal value was specified',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

        if not self._data.has_key(group):
            return MessageDialog(title='Illegal value',
                   message='The specified item does not exist',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

	if type(names)==type('s'): names=[names]
        f=self._data[group].has_key

	if 0 in map(f, names):
            return MessageDialog(title='Illegal value',
                   message='The specified item does not exist',
                   action='%s/manage_main' % REQUEST['PARENT_URL'])

	for n in names:
            del self._data[group][n]
        self.__changed__(1)
	return self._groupForm(self,REQUEST,groupName=group,
                               memberNames=self._data[group].keys())



class RoleManager:
    def roles_string(self):
	try: return join(self.__roles__)
	except: return ''

    def parse_roles_string(self, roles):
	"""Utility routine for parsing roles given as a string
	"""
	roles=map(strip,split(strip(roles)))
	try: del self.__roles__
	except: pass
	if roles=='public':
	    self.__roles__=None
	elif roles: self.__roles__=roles
