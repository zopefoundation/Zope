##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################

"""Folder object

Folders are the basic container objects and are analogous to directories.

$Id: Folder.py,v 1.56 1999/01/06 23:20:06 brian Exp $"""

__version__='$Revision: 1.56 $'[11:-2]


from Globals import HTMLFile
from ObjectManager import ObjectManager
from PropertyManager import PropertyManager
from CopySupport import CopyContainer
from FindSupport import FindSupport
from Image import Image, File
from Document import DocumentHandler
from AccessControl.Role import RoleManager
import SimpleItem
from string import rfind, lower
from content_types import content_type, find_binary, text_type
import Globals

manage_addFolderForm=HTMLFile('folderAdd', globals())

def manage_addFolder(self,id,title='',createPublic=0,createUserF=0,
                         REQUEST=None):
    """Add a new Folder object with id *id*.

    If the 'createPublic' and 'createUserF' parameters are set to any true
    value, an 'index_html' and a 'UserFolder' objects are created respectively
    in the new folder.
    """
    i=self.folderClass()()
    i.id=id
    i.title=title
    self._setObject(id,i)
    if createUserF:  i.manage_addUserFolder()
    if createPublic: i.manage_addDocument(id='index_html',title='')
    if REQUEST is not None: return self.manage_main(self,REQUEST,update_menu=1)

class Folder(ObjectManager,
             PropertyManager,
             RoleManager,
             DocumentHandler,
             SimpleItem.Item,
             CopyContainer,
             FindSupport):
    """
    The basic container object in Principia.  Folders can hold almost all
    other Principia objects.
    """
    meta_type='Folder'
    id       ='folder'
    title    ='Folder object'
    icon     ='p_/folder'

    _properties=({'id':'title', 'type': 'string'},)

    meta_types=()
    dynamic_meta_types=(
        # UserFolderHandler.meta_types_
        )

    manage_options=(
    {'label':'Contents', 'action':'manage_main',
     'target':'manage_main'},
    {'label':'Properties', 'action':'manage_propertiesForm',
     'target':'manage_main'},
    {'label':'Security', 'action':'manage_access',
     'target':'manage_main'},
    {'label':'Undo', 'action':'manage_UndoForm',
     'target':'manage_main'},
    {'label':'Find', 'action':'manage_findFrame',
     'target':'manage_main'},
    )

    __ac_permissions__=(
        ('View', ()),
        ('View management screens',
         ('manage','manage_menu','manage_main','manage_copyright',
          'manage_tabs','manage_propertiesForm','manage_UndoForm',
          'manage_cutObjects', 'manage_copyObjects', 'manage_pasteObjects',
          'manage_renameForm', 'manage_renameObject',
          'manage_findFrame', 'manage_findForm', 'manage_findAdv',
          'manage_findResult', 'manage_findOpt')),
        ('Access contents information',
         ('objectIds', 'objectValues', 'objectItems','hasProperty',
          'propertyIds', 'propertyValues','propertyItems',''),
         ('Anonymous', 'Manager'),
         ),
        ('Undo changes',       ('manage_undo_transactions',)),
        ('Change permissions',
         ('manage_access','manage_changePermissions', 'manage_role',
          'manage_permission', 'manage_defined_roles',
          'manage_acquiredForm','manage_acquiredPermissions',
          'manage_permissionForm','manage_roleForm'
          )),
        ('Delete objects',     ('manage_delObjects',)),
        ('Manage properties',
         ('manage_addProperty', 'manage_editProperties',
          'manage_delProperties', 'manage_changeProperties',)),
    )

    manage_addObject__roles__=None

    def tpValues(self):
        """Returns a list of the folder's sub-folders, used by tree tag."""
        r=[]
        if hasattr(self.aq_base,'tree_ids'):
            for id in self.aq_base.tree_ids:
                if hasattr(self, id): r.append(getattr(self, id))
        else:
            for id in self._objects:
                o=getattr(self, id['id'])
                try:
                    if o.isPrincipiaFolderish: r.append(o)
#                   if subclass(o.__class__, Folder): r.append(o)
                except: pass

        return r

    def __getitem__(self, key):
        # Hm, getattr didn't work, maybe this is a put:
        if key[:19]=='manage_draftFolder-':
            id=key[19:]
            if hasattr(self, id): return getattr(self, id).manage_supervisor()
            raise KeyError, key
        try:
            if self.REQUEST['REQUEST_METHOD']=='PUT': return PUTer(self,key)
        except: pass
        raise KeyError, key

    def folderClass(self):
        return Folder
        return self.__class__

    test_url___allow_groups__=None
    def test_url_(self):
        """Test connection"""
        return 'PING'


    # The Following methods are short-term measures to get Paul off my back;)
    def manage_exportHack(self, id=None):
        """Exports a folder and its contents to /var/export.bbe
        This file can later be imported by using manage_importHack"""
        if id is None: o=self
        else: o=getattr(self.o)
        f=Globals.data_dir+'/export.bbe'
        o._p_jar.export_file(o,f)
        return f

    def manage_importHack(self, REQUEST=None):
        "Imports a previously exported object from /var/export.bbe"
        f=Globals.data_dir+'/export.bbe'
        o=self._p_jar.import_file(f)
        id=o.id
        if hasattr(id,'im_func'): id=id()
        self._setObject(id,o)
        return 'OK, I imported %s' % id

class PUTer:
    """Class to support the HTTP PUT protocol."""

    def __init__(self, parent, key):
        self._parent=parent
        self._key=key
        self.__roles__=parent.PUT__roles__

    def PUT(self, REQUEST, BODY):
        """Adds a document, image or file to the folder when a PUT
        request is received."""
        name=self._key
        try: type=REQUEST['CONTENT_TYPE']
        except KeyError: type=''
        if not type:
            dot=rfind(name, '.')
            suf=dot > 0 and lower(name[dot+1:]) or ''
            if suf:
                try: type=content_type[suf]
                except KeyError:
                    if find_binary(BODY) >= 0: type='application/x-%s' % suf
                    else: type=text_type(BODY)
            else:
                if find_binary(BODY) >= 0:
                    raise 'Bad Request', 'Could not determine file type'
                else: type=text_type(BODY)
            __traceback_info__=suf, dot, name, type
        if lower(type)=='text/html':
            return self._parent.manage_addDocument(name,'',BODY,
                                                   REQUEST=REQUEST)
        if lower(type)[:6]=='image/':
            self._parent._setObject(name, Image(name, '', BODY, type))
        else:
            self._parent._setObject(name, File(name, '', BODY, type))
        return 'OK'

    def __str__(self): return self._key






def subclass(c,super):
    if c is super: return 1
    try:
        for base in c.__bases__:
            if subclass(base,super): return 1
    except: pass
    return 0
