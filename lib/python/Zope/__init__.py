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
"""Initialize the Zope Package and provide a published module
"""

#######################################################################
# We need to get the right BTree extensions loaded
import sys, os, App.FindHomes
sys.path.insert(0, os.path.join(SOFTWARE_HOME, 'ZopeZODB3'))
#######################################################################

import ZODB, ZODB.ZApplication, imp
import Globals, OFS.Application, sys
import AccessControl.SecurityManagement, AccessControl.User

Globals.BobobaseName = '%s/Data.fs' % Globals.data_dir
Globals.DatabaseVersion='3'

# Import products
OFS.Application.import_products()

# Open the database
try:
    # Try to use custom storage
    m=imp.find_module('custom_zodb',[INSTANCE_HOME])
except:
    import ZODB.FileStorage
    DB=ZODB.FileStorage.FileStorage(Globals.BobobaseName)
    DB=ZODB.DB(DB)
else:
    m=imp.load_module('Zope.custom_zodb', m[0], m[1], m[2])
    if hasattr(m,'DB'):
        DB=m.DB
    else:
        DB=m.Storage
        DB=ZODB.DB(DB)
        
    Globals.BobobaseName = DB.getName()
    sys.modules['Zope.custom_zodb']=m

Globals.DB=DB # Ick, this is temporary until we come up with some registry

# Hook for providing multiple transaction object manager undo support:
Globals.UndoManager=DB

Globals.opened.append(DB)
import ClassFactory
DB.setClassFactory(ClassFactory.ClassFactory)

# "Log on" as system user
AccessControl.SecurityManagement.newSecurityManager(
    None, AccessControl.User.system)

# Set up the "application" object that automagically opens
# connections
app=bobo_application=ZODB.ZApplication.ZApplicationWrapper(
    DB, 'Application', OFS.Application.Application, (),
    Globals.VersionNameName)

# Initialize products:
c=app()
OFS.Application.initialize(c)
c._p_jar.close()
del c

# "Log off" as system user
AccessControl.SecurityManagement.noSecurityManager()


# This is sneaky, but we don't want to play with Main:
sys.modules['Main']=sys.modules['Zope']

import ZODB.POSException, ZPublisher, string, ZPublisher
import ExtensionClass
from zLOG import LOG, INFO, WARNING

def debug(*args, **kw):
    return apply(ZPublisher.test,('Zope',)+args, kw)

class RequestContainer(ExtensionClass.Base):
        def __init__(self,r): self.REQUEST=r

def zpublisher_exception_hook(
    published, REQUEST, t, v, traceback,
    # static
    StringType=type(''),
    lower=string.lower,
    ConflictError=ZODB.POSException.ConflictError,
    ListType=type([]),
    ):
    try:
        if ((type(t) is StringType and
             lower(t) in ('unauthorized', 'redirect'))
            or t is SystemExit):
            raise
        if t is ConflictError:
            # now what
            # First, we need to close the current connection. We'll
            # do this by releasing the hold on it. There should be
            # some sane protocol for this, but for now we'll use
            # brute force:
            LOG('Z2 CONFLICT', INFO,
                'Competing writes at, %s' % REQUEST.get('PATH_INFO', ''),
                error=sys.exc_info())
            raise ZPublisher.Retry(t, v, traceback)
        if t is ZPublisher.Retry: v.reraise()

        if (getattr(REQUEST.get('RESPONSE', None), '_error_format', '')
            !='text/html'): raise

        if (published is None or published is app or
            type(published) is ListType):
            # At least get the top-level object
            published=app.__bobo_traverse__(REQUEST).__of__(
                RequestContainer(REQUEST))

        get_transaction().begin() # Just to be sure.

        published=getattr(published, 'im_self', published)
        while 1:
            f=getattr(published, 'raise_standardErrorMessage', None)
            if f is None:
                published=getattr(published, 'aq_parent', None)
                if published is None: raise
            else:
                break

        client=published
        while 1:
            if getattr(client, 'standard_error_message', None) is not None:
                break
            client=getattr(client, 'aq_parent', None)
            if client is None: raise

        if REQUEST.get('AUTHENTICATED_USER', None) is None:
            REQUEST['AUTHENTICATED_USER']=AccessControl.User.nobody


        f(client, REQUEST, t, v, traceback)
        
    finally: traceback=None


class TransactionsManager:
    def begin(self,
              # Optimize global var lookups:
              get_transaction=get_transaction):
        get_transaction().begin()

    def commit(self,
              # Optimize global var lookups:
               get_transaction=get_transaction):
        get_transaction().commit()

    def abort(self,
              # Optimize global var lookups:
              get_transaction=get_transaction):
        get_transaction().abort()

    def recordMetaData(self, object, request,
                       # Optimize global var lookups:
                       hasattr=hasattr, join=string.join, getattr=getattr,
                       get_transaction=get_transaction,
                       LOG=LOG, WARNING=WARNING,
                       ):
        request_get = request.get
        if hasattr(object, 'getPhysicalPath'):
            path = join(object.getPhysicalPath(), '/')
        else:
            # Try hard to get the physical path of the object,
            # but there are many circumstances where that's not possible.
            to_append = ()
            
            if hasattr(object, 'im_self') and hasattr(object, '__name__'):
                # object is a Python method.
                to_append = (object.__name__,)
                object = object.im_self
                
            while object is not None and \
                  not hasattr(object, 'getPhysicalPath'):
                if not hasattr(object, '__name__'):
                    object = None
                    break
                to_append = (object.__name__,) + to_append
                object = getattr(object, 'aq_inner', object)
                object = getattr(object, 'aq_parent', None)

            if object is not None:
                path = join(object.getPhysicalPath() + to_append, '/')
            else:
                # As Jim would say, "Waaaaaaaa!"
                # This may cause problems with virtual hosts
                # since the physical path is different from the path
                # used to retrieve the object.
                path = request_get('PATH_INFO')

        T=get_transaction()
        T.note(path)
        auth_user=request_get('AUTHENTICATED_USER',None)
        if auth_user is not None:
            try:
                auth_folder = auth_user.aq_parent
            except AttributeError:
                # Most likely some product forgot to call __of__()
                # on the user object.
                LOG('AccessControl', WARNING,
                    'A user object of type %s has no aq_parent.'
                    % str(type(auth_user)))
                auth_path = request_get('AUTHENTICATION_PATH')
            else:
                auth_path = join(auth_folder.getPhysicalPath()[1:-1], '/')
                
            T.setUser(auth_user, auth_path)
        

zpublisher_transactions_manager = TransactionsManager()

zpublisher_validated_hook=AccessControl.SecurityManagement.newSecurityManager
__bobo_before__=AccessControl.SecurityManagement.noSecurityManager
