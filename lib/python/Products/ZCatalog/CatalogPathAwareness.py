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

"""ZCatalog Findable class"""

import urllib, string
from Globals import DTMLFile
from Acquisition import aq_base

class CatalogAware:
    """ This is a Mix-In class to make objects automaticly catalog and
    uncatalog themselves in Zope, and to provide some other basic
    attributes that are useful to catalog.  Note that if your class or
    ZClass subclasses CatalogAware, it will only catalog itself when
    it is added or copied in Zope.  If you make changes to your own
    object, you are responsible for calling your object's index_object
    method. """
    
    meta_type='CatalogAware'
    default_catalog='Catalog'

    manage_editCatalogerForm=DTMLFile('editCatalogerForm', globals())

    def manage_editCataloger(self, default, REQUEST=None):
        """ """
        self.default_catalog=default
        message = "Your changes have been saved"
        if REQUEST is not None:
            return self.manage_main(self, REQUEST, manage_tabs_message=message)
    

    def manage_afterAdd(self, item, container):
        self.index_object()
        for object in self.objectValues():
            try: s=object._p_changed
            except: s=0
            object.manage_afterAdd(item, container)
            if s is None: object._p_deactivate()

    def manage_afterClone(self, item):
        self.index_object()
        for object in self.objectValues():
            try: s=object._p_changed
            except: s=0
            object.manage_afterClone(item)
            if s is None: object._p_deactivate()

    def manage_beforeDelete(self, item, container):
        self.unindex_object()
        for object in self.objectValues():
            try: s=object._p_changed
            except: s=0
            object.manage_beforeDelete(item, container)
            if s is None: object._p_deactivate()

    def creator(self):
        """Return a sequence of user names who have the local
            Owner role on an object. The name creator is used
            for this method to conform to Dublin Core."""
        users=[]
        for user, roles in self.get_local_roles():
            if 'Owner' in roles:
                users.append(user)
        return string.join(users, ', ')

    def onDeleteObject(self):
        """Object delete handler. I think this is obsoleted by
        manage_beforeDelete """
        self.unindex_object()

    def getPath(self):
        """Return the physical path for an object."""
        return string.join(self.getPhysicalPath(), '/')
    
    def summary(self, num=200):
        """Return a summary of the text content of the object."""
        if not hasattr(self, 'text_content'):
            return ''
        attr=getattr(self, 'text_content')
        if callable(attr):
            text=attr()
        else: text=attr
        n=min(num, len(text))
        return text[:n]

    def index_object(self):
        """A common method to allow Findables to index themselves."""
        if hasattr(self, self.default_catalog):
            getattr(self,
                    self.default_catalog).catalog_object(self, self.getPath())

    def unindex_object(self):
        """A common method to allow Findables to unindex themselves."""
        if hasattr(self, self.default_catalog):
            getattr(self,
                    self.default_catalog).uncatalog_object(self.getPath())

    def reindex_object(self):
        """ Suprisingly useful """
        self.unindex_object()
        self.index_object()

    def reindex_all(self, obj=None):
        """ """
        if obj is None: obj=self
        if hasattr(aq_base(obj), 'index_object'):
            obj.index_object()
        if hasattr(aq_base(obj), 'objectValues'):
            sub=obj.objectValues()
            for item in obj.objectValues():
                reindex_all(self, item)
        return 'done!'









