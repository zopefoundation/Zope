"""Access control package"""

__version__='$Revision: 1.7 $'[11:-2]

import Globals
from User import SafeDtml
from Globals import MessageDialog
from string import join, strip, split


class RoleManager:
    """Mixin role management support"""

    manage_rolesForm=SafeDtml('AccessControl/manage_rolesForm')
    smallRolesWidget=SafeDtml('AccessControl/smallRolesWidget')


    def selectedRoles(self):
	try:    roles=self.aq_self.__roles__
	except: roles=[]
	if roles is None: roles=[]
	return map(lambda i, r=roles:
		   i in r and ('<OPTION VALUE="%s" SELECTED>%s' % (i,i)) \
		   or  ('<OPTION VALUE="%s">%s' % (i,i)), self.validRoles())

    def aclAChecked(self):
	if hasattr(self,'aq_self'):
	    self=self.aq_self
	try:    roles=self.__roles__
	except: return ' CHECKED'
	return ''

    def aclPChecked(self):
	if hasattr(self,'aq_self'):
	    self=self.aq_self
	try:    roles=self.__roles__
	except: return ''
	if roles is None: 
	    return ' CHECKED'
	return ''

    def aclEChecked(self):
	if hasattr(self,'aq_self'):
	    self=self.aq_self
	try:    roles=self.__roles__
	except: return 0
	if roles is None: 
	    return ''
	return ' CHECKED'


    def manage_editRoles(self,REQUEST,acl_type='A',acl_roles=[]):
        """ """
	if hasattr(self,'aq_self'):
	    try:    del self.aq_self.__roles__
	    except: pass
	if acl_type=='A':
	    return self.manage_rolesForm(self,REQUEST)
	if acl_type=='P':
	    self.__roles__=None
	    return self.manage_rolesForm(self,REQUEST)
	if not acl_roles:
	    raise 'Bad Request','No roles specified!'
	self.__roles__=acl_roles
        return self.manage_rolesForm(self,REQUEST)


    def _setRoles(self,acl_type,acl_roles):
	# Non-web helper to correctly set roles
	if hasattr(self,'aq_self'):
	    try:    del self.aq_self.__roles__
	    except: pass
	if acl_type=='A':
	    return
	if acl_type=='P':
	    self.__roles__=None
	    return
	if not acl_roles:
	    raise 'Bad Request','No roles specified!'
	self.__roles__=acl_roles




# $Log: Role.py,v $
# Revision 1.7  1997/12/05 17:10:08  brian
# New UI
#
# Revision 1.6  1997/11/18 21:48:20  brian
# Fixed bug that appeared after __roles__ were allowed to be acquired.
#
# Revision 1.5  1997/11/07 17:10:03  brian
# Moved validRoles manage_addRole and manage_deleteRole to app object
#
# Revision 1.4  1997/11/06 22:45:26  brian
# Added global roles to app
#
# Revision 1.3  1997/09/08 23:01:33  brian
# Style mods
#
# Revision 1.2  1997/09/02 18:12:13  jim
# Added smallRolesWidget.
#
# Revision 1.1  1997/08/29 18:34:53  brian
# Added basic role management to package.
#
