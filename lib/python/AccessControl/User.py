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
"""Access control package"""

__version__='$Revision: 1.76 $'[11:-2]

import Globals, App.Undo, socket, regex
from Globals import HTMLFile, MessageDialog, Persistent, PersistentMapping
from string import join,strip,split,lower
from App.Management import Navigation, Tabs
from Acquisition import Implicit
from OFS.SimpleItem import Item
from base64 import decodestring
from App.ImageFile import ImageFile
from Role import RoleManager
from string import split, join
from PermissionRole import _what_not_even_god_should_do

ListType=type([])




NotImplemented='NotImplemented'



class BasicUser(Implicit):
    """Base class for all User objects"""
    
    # ----------------------------
    # Public User object interface
    # ----------------------------

    def __init__(self,name,password,roles,domains):
        raise NotImplemented

    def getUserName(self):
        """Return the username of a user"""
        raise NotImplemented

    def _getPassword(self):
        """Return the password of the user."""
        raise NotImplemented

    def getRoles(self):
        """Return the list of roles assigned to a user."""
        raise NotImplemented

    def getRolesInContext(self, object):
        """Return the list of roles assigned to the user,
           including local roles assigned in context of
           the passed in object."""
        name=self.getUserName()
        roles=self.getRoles()
        local={}
        while 1:
            if hasattr(object, '__ac_local_roles__'):
                dict=object.__ac_local_roles__ or {}
                for r in dict.get(name, []):
                    local[r]=1
            if not hasattr(object, 'aq_parent'):
                break
            object=object.aq_parent
        joined=rolejoin(roles, local.keys())
        return joined


    def getDomains(self):
        """Return the list of domain restrictions for a user"""
        raise NotImplemented

    # ------------------------------
    # Internal User object interface
    # ------------------------------
    
    def authenticate(self, password, request):
        domains=self.getDomains()
        passwrd=self._getPassword()
        if domains:
            return (password==passwrd) and domainSpecMatch(domains, request)
        return password==passwrd

    def _shared_roles(self, parent):
        r=[]
        while 1:
            if hasattr(parent,'__roles__'):
                roles=parent.__roles__
                if roles is None: return 'Anonymous',
                if 'Shared' in roles:
                    roles=list(roles)
                    roles.remove('Shared')
                    r=r+roles
                else:
                    try: return r+list(roles)
                    except: return r
            if hasattr(parent, 'aq_parent'):
                while hasattr(parent.aq_self,'aq_self'):
                    parent=parent.aq_self
                parent=parent.aq_parent
            else: return r

    def allowed(self, parent, roles=None):
        """Check whether the user has access to parent, assuming that
           parent.__roles__ is the given roles."""
        if roles is None or 'Anonymous' in roles:
            return 1
        usr_roles=self.getRolesInContext(parent)
        for role in roles:
            if role in usr_roles:
                if (hasattr(self,'aq_parent') and
                    hasattr(self.aq_parent,'aq_parent')):
                    if parent is None: return 1
                    if (not hasattr(parent, 'aq_inContextOf') and
                        hasattr(parent, 'im_self')):
                        # This is a method, grab it's self.
                        parent=parent.im_self
                    if not parent.aq_inContextOf(self.aq_parent.aq_parent,1):
                        if 'Shared' in roles:
                            # Damn, old role setting. Waaa
                            roles=self._shared_roles(parent)
                            if 'Anonymous' in roles: return 1
                        return None
                return 1

        if 'Shared' in roles:
            # Damn, old role setting. Waaa
            roles=self._shared_roles(parent)
            if roles is None or 'Anonymous' in roles: return 1
            while 'Shared' in roles: roles.remove('Shared')
            return self.allowed(parent,roles)

        return None

    hasRole=allowed
    domains=[]
    
    def has_role(self, roles, object=None):
        """Check to see if a user has a given role or roles."""
        if type(roles)==type('s'):
            roles=[roles]
        if object is not None:
            # Check in object for local roles.
            user = self.getUserName()
            dict = object.__ac_local_roles__ or {}
            if dict.has_key(user):
                local_roles = dict[user]
                for role in roles:
                    if role in local_roles:
                        return 1
        # No local roles, try global roles...
        user_roles=self.getRoles()
        for role in roles:
            if role in user_roles:
                return 1
        return 0

    def __len__(self): return 1
    def __str__(self): return self.getUserName()
    __repr__=__str__




class User(BasicUser, Persistent):
    """Standard Principia User object"""

    def __init__(self,name,password,roles,domains):
        self.name   =name
        self.__     =password
        self.roles  =roles
        self.domains=domains

    def getUserName(self):
        """Return the username of a user"""
        return self.name

    def _getPassword(self):
        """Return the password of the user."""
        return self.__

    def getRoles(self):
        """Return the list of roles assigned to a user."""
        return self.roles

    def getDomains(self):
        """Return the list of domain restrictions for a user"""
        return self.domains


class Super(User):
    """Super user
    """
    def allowed(self,parent,roles=None):
        return roles is not _what_not_even_god_should_do

    hasRole=allowed

    def has_role(self, roles): return 1

_remote_user_mode=0
try:
    f=open('%s/access' % INSTANCE_HOME, 'r')
    data=split(strip(f.readline()),':')
    f.close()
    _remote_user_mode=not data[1]
    try:    ds=split(data[2], ' ')
    except: ds=[]
    super=Super(data[0],data[1],('manage',), ds)
    del data
except:
    raise 'InstallError', 'No access file found - see INSTALL.txt'


nobody=User('Anonymous User','',('Anonymous',), [])


class BasicUserFolder(Implicit, Persistent, Navigation, Tabs, RoleManager,
                      Item, App.Undo.UndoSupport):
    """Base class for UserFolder-like objects"""

    meta_type='User Folder'
    id       ='acl_users'
    title    ='User Folder'

    isPrincipiaFolderish=1
    isAUserFolder=1

    manage_options=(
    {'label':'Contents', 'action':'manage_main'},
    {'label':'Security', 'action':'manage_access'},
    {'label':'Undo',     'action':'manage_UndoForm'},
    )

    __ac_permissions__=(
        ('Manage users', ('manage_users','getUserNames','getUser','getUsers',
                          )),
        )

    # ----------------------------------
    # Public UserFolder object interface
    # ----------------------------------
    
    def getUserNames(self):
        """Return a list of usernames"""
        raise NotImplemented

    def getUsers(self):
        """Return a list of user objects"""
        raise NotImplemented

    def getUser(self, name):
        """Return the named user object or None"""
        raise NotImplemented

    def _doAddUser(self, name, password, roles, domains):
        """Create a new user"""
        raise NotImplemented

    def _doChangeUser(self, name, password, roles, domains):
        """Modify an existing user"""
        raise NotImplemented

    def _doDelUsers(self, names):
        """Delete one or more users"""
        raise NotImplemented


    # -----------------------------------
    # Private UserFolder object interface
    # -----------------------------------


    _remote_user_mode=_remote_user_mode
    _super=super
    _nobody=nobody
            
    def validate(self,request,auth='',roles=None):

        if roles is _what_not_even_god_should_do:
            request.response.notFoundError()
        
        parents=request.get('PARENTS', [])
        if not parents:
            parent=self.aq_parent
        else: parent=parents[0]

        # If no authorization, only a user with a
        # domain spec and no passwd or nobody can
        # match
        if not auth:
            for ob in self.getUsers():
                domains=ob.getDomains()
                if domains:
                    if ob.authenticate('', request):
                        if ob.allowed(parent, roles):
                            ob=ob.__of__(self)
                            return ob
            nobody=self._nobody
            if self._isTop() and nobody.allowed(parent, roles):
                ob=nobody.__of__(self)
                return ob
            return None

        # Only do basic authentication
        if lower(auth[:6])!='basic ':
            return None
        name,password=tuple(split(decodestring(split(auth)[-1]), ':', 1))

        # Check for superuser
        super=self._super
        if self._isTop() and (name==super.getUserName()) and \
        super.authenticate(password, request):
            return super

        # Try to get user
        user=self.getUser(name)
        if user is None:
            return None

        # Try to authenticate user
        if not user.authenticate(password, request):
            return None

        # We need the user to be able to acquire!
        user=user.__of__(self)

        # Try to authorize user
        if user.allowed(parent, roles):
            return user
        return None


    if _remote_user_mode:
        
        def validate(self,request,auth='',roles=None):
            parent=request['PARENTS'][0]
            e=request.environ
            if e.has_key('REMOTE_USER'):
                name=e['REMOTE_USER']
            else:
                for ob in self.getUsers():
                    domains=ob.getDomains()
                    if domains:
                        if ob.authenticate('', request):
                            if ob.allowed(parent, roles):
                                ob=ob.__of__(self)
                                return ob
                nobody=self._nobody
                if self._isTop() and nobody.allowed(parent, roles):
                    ob=nobody.__of__(self)
                    return ob
                return None

            # Check for superuser
            super=self._super
            if self._isTop() and (name==super.getUserName()):
                return super

            # Try to get user
            user=self.getUser(name)
            if user is None:
                return None

            # We need the user to be able to acquire!
            user=user.__of__(self)

            # Try to authorize user
            if user.allowed(parent, roles):
                return user
            return None


    def _isTop(self):
        try: return self.aq_parent.aq_base.isTopLevelPrincipiaApplicationObject
        except: return 0

    def __len__(self):
        return 1

    _mainUser=HTMLFile('mainUser', globals())
    _add_User=HTMLFile('addUser', globals(),
                       remote_user_mode__=_remote_user_mode)
    _editUser=HTMLFile('editUser', globals(),
                       remote_user_mode__=_remote_user_mode)
    manage=manage_main=_mainUser

    def domainSpecValidate(self, spec):
        for ob in spec:
            sz=len(ob)
            if not ((addr_match(ob) == sz) or (host_match(ob) == sz)):
                return 0
        return 1

    def _addUser(self,name,password,confirm,roles,domains,REQUEST=None):
        if not name:
            return MessageDialog(
                   title  ='Illegal value', 
                   message='A username must be specified',
                   action ='manage_main')
        if not password or not confirm:
            if not domains:
                return MessageDialog(
                   title  ='Illegal value', 
                   message='Password and confirmation must be specified',
                   action ='manage_main')
        if self.getUser(name) or (name==self._super.getUserName()):
            return MessageDialog(
                   title  ='Illegal value', 
                   message='A user with the specified name already exists',
                   action ='manage_main')
        if (password or confirm) and (password != confirm):
            return MessageDialog(
                   title  ='Illegal value', 
                   message='Password and confirmation do not match',
                   action ='manage_main')
        
        if not roles: roles=[]
        if not domains: domains=[]

        if domains and not self.domainSpecValidate(domains):
            return MessageDialog(
                   title  ='Illegal value', 
                   message='Illegal domain specification',
                   action ='manage_main')
        self._doAddUser(name, password, roles, domains)        
        if REQUEST: return self._mainUser(self, REQUEST)


    def _changeUser(self,name,password,confirm,roles,domains,REQUEST=None):
        if not name:
            return MessageDialog(
                   title  ='Illegal value', 
                   message='A username must be specified',
                   action ='manage_main')
        if not password or not confirm:
            if not domains:
                return MessageDialog(
                   title  ='Illegal value', 
                   message='Password and confirmation must be specified',
                   action ='manage_main')
        if not self.getUser(name):
            return MessageDialog(
                   title  ='Illegal value', 
                   message='Unknown user',
                   action ='manage_main')
        if (password or confirm) and (password != confirm):
            return MessageDialog(
                   title  ='Illegal value', 
                   message='Password and confirmation do not match',
                   action ='manage_main')

        if not roles: roles=[]
        if not domains: domains=[]

        if domains and not self.domainSpecValidate(domains):
            return MessageDialog(
                   title  ='Illegal value', 
                   message='Illegal domain specification',
                   action ='manage_main')
        self._doChangeUser(name, password, roles, domains)
        if REQUEST: return self._mainUser(self, REQUEST)

    def _delUsers(self,names,REQUEST=None):
        if not names:
            return MessageDialog(
                   title  ='Illegal value', 
                   message='No users specified',
                   action ='manage_main')
        self._doDelUsers(names)
        if REQUEST: return self._mainUser(self, REQUEST)

    def manage_users(self,submit=None,REQUEST=None,RESPONSE=None):
        """ """
        if submit=='Add...':
            return self._add_User(self, REQUEST)

        if submit=='Edit':
            try:    user=self.getUser(reqattr(REQUEST, 'name'))
            except: return MessageDialog(
                    title  ='Illegal value',
                    message='The specified user does not exist',
                    action ='manage_main')
            return self._editUser(self,REQUEST,user=user,password=user.__)

        if submit=='Add':
            name    =reqattr(REQUEST, 'name')
            password=reqattr(REQUEST, 'password')
            confirm =reqattr(REQUEST, 'confirm')
            roles   =reqattr(REQUEST, 'roles')
            domains =reqattr(REQUEST, 'domains')
            return self._addUser(name,password,confirm,roles,domains,REQUEST)

        if submit=='Change':
            name    =reqattr(REQUEST, 'name')
            password=reqattr(REQUEST, 'password')
            confirm =reqattr(REQUEST, 'confirm')
            roles   =reqattr(REQUEST, 'roles')
            domains =reqattr(REQUEST, 'domains')
            return self._changeUser(name,password,confirm,roles,
                                    domains,REQUEST)

        if submit=='Delete':
            names=reqattr(REQUEST, 'names')
            return self._delUsers(names,REQUEST)

        return self._mainUser(self, REQUEST)

    def user_names(self):
        return self.getUserNames()

    # Copy/Paste support

    def _notifyOfCopyTo(self, container, op=0):
        if hasattr(container, '__allow_groups__'):
            raise TypeError, (
                'Target already contains a UserFolder.')

    def _postCopy(self, container, op=0):
        container.__allow_groups__=container.acl_users

    def _setId(self, id):
        if id != self.id:
            raise Globals.MessageDialog(
                title='Invalid Id',
                message='Cannot change the id of a UserFolder',
                action ='./manage_main',)









class UserFolder(BasicUserFolder):
    """Standard Principia UserFolder object

    A UserFolder holds User objects which contain information
    about users including name, password domain, and roles.
    UserFolders function chiefly to contol access by authenticating
    users and binding them to a collection of roles."""

    meta_type='User Folder'
    id       ='acl_users'
    title    ='User Folder'
    icon     ='p_/UserFolder'

    def __init__(self):
        self.data=PersistentMapping()

    def getUserNames(self):
        """Return a list of usernames"""
        names=self.data.keys()
        names.sort()
        return names

    def getUsers(self):
        """Return a list of user objects"""
        data=self.data
        names=data.keys()
        names.sort()
        users=[]
        f=users.append
        for n in names:
            f(data[n])
        return users

    def getUser(self, name):
        """Return the named user object or None"""
        if self.data.has_key(name):
            return self.data[name]
        return None

    def _doAddUser(self, name, password, roles, domains):
        """Create a new user"""
        self.data[name]=User(name,password,roles,domains)

    def _doChangeUser(self, name, password, roles, domains):
        user=self.data[name]
        user.__=password
        user.roles=roles
        user.domains=domains

    def _doDelUsers(self, names):
        for name in names:
            del self.data[name]









def manage_addUserFolder(self,dtself=None,REQUEST=None,**ignored):
    """ """
    f=UserFolder()
    try:    self._setObject('acl_users', f)
    except: return MessageDialog(
                   title  ='Item Exists',
                   message='This object already contains a User Folder',
                   action ='%s/manage_main' % REQUEST['URL1'])
    self.__allow_groups__=f
    
    if REQUEST: return self.manage_main(self,REQUEST,update_menu=1)






def rolejoin(roles, other):
    dict={}
    for role in roles:
        dict[role]=1
    for role in other:
        dict[role]=1
    roles=dict.keys()
    roles.sort()
    return roles

addr_match=regex.compile('[0-9\.\*]*').match
host_match=regex.compile('[A-Za-z0-9\.\*]*').match


def domainSpecMatch(spec, request):
    host=''
    addr=''

    if request.has_key('REMOTE_HOST'):
        host=request['REMOTE_HOST']

    if request.has_key('REMOTE_ADDR'):
        addr=request['REMOTE_ADDR']

    if not host and not addr:
        return 0

    if not host:
        try:    host=socket.gethostbyaddr(addr)[0]
        except: pass
    if not addr:
        try:    addr=socket.gethostbyname(host)
        except: pass

    _host=split(host, '.')
    _addr=split(addr, '.')
    _hlen=len(_host)
    _alen=len(_addr)
    
    for ob in spec:
        sz=len(ob)
        _ob=split(ob, '.')
        _sz=len(_ob)

        if addr_match(ob)==sz:
            fail=0
            for i in range(_sz):
                a=_addr[i]
                o=_ob[i]
                if (o != a) and (o != '*'):
                    fail=1
                    break
            if fail:
                continue
            return 1

        if host_match(ob)==sz:
            if _hlen < _sz:
                continue
            elif _hlen > _sz:
                _item=_host[-_sz:]
            else:
                _item=_host
            fail=0
            for i in range(_sz):
                h=_item[i]
                o=_ob[i]
                if (o != h) and (o != '*'):
                    fail=1
                    break
            if fail:
                continue
            return 1
    return 0


def absattr(attr):
    if callable(attr): return attr()
    return attr

def reqattr(request, attr):
    try:    return request[attr]
    except: return None
