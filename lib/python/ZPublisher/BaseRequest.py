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
__version__='$Revision: 1.8 $'[11:-2]

from string import join, split, find, rfind, lower, upper
from urllib import quote

UNSPECIFIED_ROLES=''

try:
    from ExtensionClass import Base
    class RequestContainer(Base):
        def __init__(self,**kw):
            for k,v in kw.items(): self.__dict__[k]=v

        def manage_property_types(self):
            return type_converters.keys()
            
except:
    class RequestContainer:
        def __init__(self,**kw):
            for k,v in kw.items(): self.__dict__[k]=v

_marker=[]
class BaseRequest:
    """Provide basic ZPublisher request management
    
    This object provides access to request data. Request data may
    vary depending on the protocol used.

    Request objects are created by the object publisher and will be
    passed to published objects through the argument name, REQUEST.

    The request object is a mapping object that represents a
    collection of variable to value mappings.
    """

    common={} # Common request data
    _auth=None

    def __init__(self, other=None, **kw):
        if other is None: other=kw
        else:
            for k, v in kw.items(): other[k]=v
        self.other=other

    def __setitem__(self,key,value):
        """Set application variables

        This method is used to set a variable in the requests "other"
        category.
        """
        self.other[key]=value

    set=__setitem__

    def __getitem__(self,key,
                    default=_marker, # Any special internal marker will do
                    ):
        """Get a variable value

        Return a value for the required variable name.
        The value will be looked up from one of the request data
        categories. The search order is environment variables,
        other variables, form data, and then cookies. 
        
        """
        if key=='REQUEST': return self

        v=self.other.get(key, _marker)
        if v is not _marker: return v
        v=self.common.get(key, default)
        if v is not _marker: return v
        raise KeyError, key

    __getattr__=get=__getitem__

    def has_key(self,key):
        return self.get(key, _marker) is not _marker

    def keys(self):
        keys = {}
        keys.update(self.common)
        keys.update(self.other)
        return keys.keys()

    def items(self):
        result = []
        get=self.get
        for k in self.keys():
            result.append((k, get(k)))
        return result

    def values(self):
        result = []
        get=self.get
        for k in self.keys():
            result.append(get(k))
        return result

    def __str__(self):

        return join(map(lambda item: "%s:\t%s" % item, self.items()), "\n")

    __repr__=__str__


    def traverse(self, path, response=None):
        """Traverse the object space

        The REQUEST must already have a PARENTS item with at least one
        object in it.  This is typically the root object.
        """
        request=self
        request_get=request.get
        if response is None: response=self.response
        debug_mode=response.debug_mode

        if path[:1] != '/': path='/'+path
        if path[-1:] != '/': path=path+'/'
        if find(path,'/.') >= 0:
            path=join(split(path,'/./'),'/')
            l=find(path,'/../',1)
            while l > 0:
                p1=path[:l]
                path=path[:rfind(p1,'/')+1]+path[l+4:]
                l=find(path,'/../',1)
        path=path[1:-1]
    
        path=split(path,'/')
        while path and not path[0]: path = path[1:]
    
        method=req_method=upper(request_get('REQUEST_METHOD', 'GET'))
        baseflag=0
        if method=='GET' or method=='POST':
            method='index_html'
        else: baseflag=1
        URL=request['URL']
    
        parents=request['PARENTS']
        object=parents[-1]
        del parents[-1]
    
        if hasattr(object,'__roles__'): roles=object.__roles__
        else:                           roles=UNSPECIFIED_ROLES
    
        # if the top object has a __bobo_traverse__ method, then use it
        # to possibly traverse to an alternate top-level object.
        if hasattr(object,'__bobo_traverse__'):
            try: object=object.__bobo_traverse__(request)
            except: pass            
    
        # Get default object if no path was specified:
        if not path:
            if not method: return response.forbiddenError(entry_name)
            entry_name=method
            try:
                if hasattr(object,entry_name):
                    response.setBase(URL)
                    path=[entry_name]
                else:
                    try:
                        if object.has_key(entry_name):
                            path=[entry_name]
                    except: pass
            except: pass
    
        # Traverse the URL to find the object:
    
        if hasattr(object, '__of__'): 
            # Try to bind the top-level object to the request
            object=object.__of__(RequestContainer(REQUEST=request))
    
        steps=[]
        path.reverse()
        while path:
            entry_name=path[-1]
            del path[-1]
            URL="%s/%s" % (URL,quote(entry_name))
            got=0
            if entry_name:
                if entry_name[:1]=='_':
                    if debug_mode:
                        return response.debugError(
                            "Object name begins with an underscore at: %s"
                            % URL)
                    else: return response.forbiddenError(entry_name)
    
                if hasattr(object,'__bobo_traverse__'):
                    request['URL']=URL
                    subobject=object.__bobo_traverse__(request,entry_name)
                    if type(subobject) is type(()) and len(subobject) > 1:
                        while len(subobject) > 2:
                            parents.append(subobject[0])
                            subobject=subobject[1:]
                        object, subobject = subobject
                else:
                    try:
                        # Note - this is necessary to support things like DAV.
                        # We have to make sure that the target object is not
                        # acquired if the request_method is other than GET or
                        # POST. Otherwise, you could never use PUT to add a new
                        # object named 'test' if an object 'test' existed above
                        # it in the heirarchy -- you'd always get the existing
                        # object :(
                        if baseflag and hasattr(object, 'aq_base'):
                            if hasattr(object.aq_base, entry_name):
                                subobject=getattr(object, entry_name)
                            else: raise AttributeError, entry_name
                        else: subobject=getattr(object, entry_name)
                    except AttributeError:
                        got=1
                        try: subobject=object[entry_name]
                        except (KeyError, IndexError,
                                TypeError, AttributeError):
                            if debug_mode:
                                return response.debugError(
                                    "Cannot locate object at: %s" %URL) 
                            else: return response.notFoundError(URL)
    
                try:
                    try: doc=subobject.__doc__
                    except: doc=getattr(object, entry_name+'__doc__')
                    if not doc: raise AttributeError, entry_name
                except:
                    if debug_mode:
                        return response.debugError("Missing doc string at: %s"
                                                   % URL)
                    else: return response.notFoundError("%s" % (URL))

                if hasattr(subobject,'__roles__'):
                    roles=subobject.__roles__
                else:
                    if not got:
                        roleshack=entry_name+'__roles__'
                        if hasattr(object, roleshack):
                            roles=getattr(object, roleshack)

                # Promote subobject to object
            
                parents.append(object)
                object=subobject

                steps.append(entry_name)
    
                # Check for method:
                if not path:
                    if (method and hasattr(object,method)
                        and entry_name != method
                        and getattr(object, method) is not None
                        ):
                        request._hacked_path=1
                        path=[method]
                    else:
                        if (hasattr(object, '__call__') and
                            hasattr(object.__call__,'__roles__')):
                            roles=object.__call__.__roles__
                        if request._hacked_path:
                            i=rfind(URL,'/')
                            if i > 0: response.setBase(URL[:i])
    
    
        # THIS LOOKS WRONG!
#        if entry_name != method and method != 'index_html':
#            if debug_mode:
#                response.debugError("Method %s not found at: %s"
#                                    % (method,URL))
#            else: response.notFoundError(method)
    
        request.steps=steps
        parents.reverse()
    
        # Do authorization checks
        user=groups=None
        i=0
        if roles is not None:
    
            last_parent_index=len(parents)
            if hasattr(object, '__allow_groups__'):
                groups=object.__allow_groups__
                inext=0
            else:
                inext=None
                for i in range(last_parent_index):
                    if hasattr(parents[i],'__allow_groups__'):
                        groups=parents[i].__allow_groups__
                        inext=i+1
                        break
    
            if inext is not None:
                i=inext
    
                if hasattr(groups, 'validate'): v=groups.validate
                else: v=old_validation
    
                auth=request._auth
    
                if v is old_validation and roles is UNSPECIFIED_ROLES:
                    # No roles, so if we have a named group, get roles from
                    # group keys
                    if hasattr(groups,'keys'): roles=groups.keys()
                    else:
                        try: groups=groups()
                        except: pass
                        try: roles=groups.keys()
                        except: pass
    
                    if groups is None:
                        # Public group, hack structures to get it to validate
                        roles=None
                        auth=''
    
                if v is old_validation:
                    user=old_validation(groups, request, auth, roles)
                elif roles is UNSPECIFIED_ROLES: user=v(request, auth)
                else: user=v(request, auth, roles)
    
                while user is None and i < last_parent_index:
                    parent=parents[i]
                    i=i+1
                    if hasattr(parent, '__allow_groups__'): 
                        groups=parent.__allow_groups__
                    else: continue
                    if hasattr(groups,'validate'): v=groups.validate
                    else: v=old_validation
                    if v is old_validation:
                        user=old_validation(groups, request, auth, roles)
                    elif roles is UNSPECIFIED_ROLES: user=v(request, auth)
                    else: user=v(request, auth, roles)
                    
            if user is None and roles != UNSPECIFIED_ROLES:
                response.unauthorized()
    
        steps=join(steps[:-i],'/')
        if user is not None:
            request['AUTHENTICATED_USER']=user
            request['AUTHENTICATION_PATH']=steps

        # Remove http request method from the URL.
        request['URL']=URL
    
        return object

def old_validation(groups, request, auth,
                   roles=UNSPECIFIED_ROLES):

    if auth:
        auth=request._authUserPW()
        if auth: name,password = auth
        elif roles is None: return ''
        else: return None
    elif request.environ.has_key('REMOTE_USER'):
        name=request.environ['REMOTE_USER']
        password=None
    else:
        if roles is None: return ''
        return None

    if roles is None: return name

    keys=None
    try:
        keys=groups.keys
    except:
        try:
            groups=groups() # Maybe it was a method defining a group
            keys=groups.keys
        except: pass

    if keys is not None:
        # OK, we have a named group, so apply the roles to the named
        # group.
        if roles is UNSPECIFIED_ROLES: roles=keys()
        g=[]
        for role in roles:
            if groups.has_key(role): g.append(groups[role])
        groups=g

    for d in groups:
        if d.has_key(name) and (d[name]==password or password is None):
            return name

    if keys is None:
        # Not a named group, so don't go further
        raise 'Forbidden', (
            """<strong>You are not authorized to access this resource""")

    return None

