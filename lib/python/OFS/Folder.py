##############################################################################
# 
# Zope Public License (ZPL) Version 0.9.6
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
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
# 3. Any use, including use of the Zope software to operate a website,
#    must either comply with the terms described below under
#    "Attribution" or alternatively secure a separate license from
#    Digital Creations.  Digital Creations will not unreasonably
#    deny such a separate license in the event that the request
#    explains in detail a valid reason for withholding attribution.
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
# Attribution
# 
#   Individuals or organizations using this software as a web
#   site ("the web site") must provide attribution by placing
#   the accompanying "button" on the website's main entry
#   point.  By default, the button links to a "credits page"
#   on the Digital Creations' web site. The "credits page" may
#   be copied to "the web site" in order to add other credits,
#   or keep users "on site". In that case, the "button" link
#   may be updated to point to the "on site" "credits page".
#   In cases where this placement of attribution is not
#   feasible, a separate arrangment must be concluded with
#   Digital Creations.  Those using the software for purposes
#   other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.  Where
#   attribution is not possible, or is considered to be
#   onerous for some other reason, a request should be made to
#   Digital Creations to waive this requirement in writing.
#   As stated above, for valid requests, Digital Creations
#   will not unreasonably deny such requests.
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

"""Folder object

Folders are the basic container objects and are analogous to directories.

$Id: Folder.py,v 1.67 1999/03/04 17:44:51 brian Exp $"""

__version__='$Revision: 1.67 $'[11:-2]

import Globals, SimpleItem, Acquisition, mimetypes, content_types
from Globals import HTMLFile
from ObjectManager import ObjectManager
from PropertyManager import PropertyManager
from AccessControl.Role import RoleManager
from webdav.NullResource import NullResource
from webdav.Collection import Collection
from CopySupport import CopyContainer
from FindSupport import FindSupport
from Image import Image, File
from App.Dialogs import MessageDialog
from string import find, rfind, lower
import marshal
from cStringIO import StringIO
import os

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
    if createPublic: i.manage_addDTMLDocument(id='index_html',title='')
    if REQUEST is not None: return self.manage_main(self,REQUEST,update_menu=1)

class Folder(ObjectManager, PropertyManager, RoleManager, Collection,
             SimpleItem.Item, CopyContainer, FindSupport):
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
        {'label':'Contents', 'action':'manage_main'},
        {'label':'Properties', 'action':'manage_propertiesForm'},
        {'label':'Import/Export', 'action':'manage_importExportForm'},
        {'label':'Security', 'action':'manage_access'},
        {'label':'Undo', 'action':'manage_UndoForm'},
        {'label':'Find', 'action':'manage_findFrame'},
    )

    __ac_permissions__=(
        ('View', ()),
        ('View management screens',
         ('manage','manage_menu','manage_main','manage_copyright',
          'manage_tabs','manage_propertiesForm','manage_UndoForm',
          'manage_cutObjects', 'manage_copyObjects', 'manage_pasteObjects',
          'manage_renameForm', 'manage_renameObject',
          'manage_findFrame', 'manage_findForm', 'manage_findAdv',
          'manage_findResult')),
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
        ('Delete objects',     ('manage_delObjects', 'DELETE')),
        ('Manage properties',
         ('manage_addProperty', 'manage_editProperties',
          'manage_delProperties', 'manage_changeProperties',)),
        ('FTP access',         ('manage_FTPstat','manage_FTPlist')),
        ('Import/Export objects',
         ('manage_importObject','manage_importExportForm',
          'manage_exportObject')
         ),

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
        if hasattr(self, 'REQUEST'):
            method=self.REQUEST.get('REQUEST_METHOD', 'GET')
            if not method in ('GET', 'POST'):
                return NullResource(self, key).__of__(self)
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

    # These methods replace manage_importHack and manage_exportHack

    def manage_exportObject(self, id='', download=None, RESPONSE=None):
        """Exports an object to a file and returns that file."""        
        if not id:
            id=self.id
            if callable(id): id=id()
            ob=self
        else: ob=getattr(self,id)
        if download:
            f=StringIO()
            ob._p_jar.export_file(ob, f)
            RESPONSE.setHeader('Content-type','application/data')
            RESPONSE.setHeader('Content-Disposition',
                'inline;filename=%s.bbe' % id)
            return f.getvalue()
        f=Globals.data_dir+'/%s.bbe' % id
        ob._p_jar.export_file(ob, f)
        if RESPONSE is not None:
            return MessageDialog(
                    title="Object exported",
                    message="<EM>%s</EM> sucessfully\
                    exported to <pre>%s</pre>." % (id, f),
                    action="manage_main")

    manage_importExportForm=HTMLFile('importExport',globals())

    def manage_importObject(self, file, REQUEST=None):
        """Import an object from a file"""
        dirname, file=os.path.split(file)
        if dirname:
            raise 'Bad Request', 'Invalid file name %s' % file
        file=os.path.join(INSTANCE_HOME, 'import', file)
        if not os.path.exists(file):
            raise 'Bad Request', 'File does not exist: %s' % file
        ob=self._p_jar.import_file(file)
        if REQUEST: self._verifyObjectPaste(ob, REQUEST)
        id=ob.id
        if hasattr(id, 'im_func'): id=id()
        self._setObject(id, ob)
        if REQUEST is not None:
            return MessageDialog(
                title='Object imported',
                message='<EM>%s</EM> sucessfully imported' % id,
                action='manage_main'
                )

    # FTP support methods
    
    def manage_FTPlist(self,REQUEST):
        "Directory listing for FTP"
        out=()
        # check to see if we are acquiring our objectValues or not
        if len(REQUEST.PARENTS) > 1 and \
                self.objectValues()==REQUEST.PARENTS[1].objectValues():
                raise ValueError, 'FTP List not supported on acquired objects'
                # XXX what type of error to raise?  
        files=self.objectItems()
        if not (hasattr(self,'isTopLevelPrincipiaApplicationObject') and
                self.isTopLevelPrincipiaApplicationObject):
            files.insert(0,('..',self.aq_parent))
        for k,v in files:
            stat=marshal.loads(v.manage_FTPstat(REQUEST))
            out=out+((k,stat),)
        return marshal.dumps(out)   

    def manage_FTPstat(self,REQUEST):
        "Psuedo stat used for FTP listings"
        mode=0040000
        from AccessControl.User import nobody
        # check to see if we are acquiring our objectValues or not
        if not (len(REQUEST.PARENTS) > 1 and
                self.objectValues() == REQUEST.PARENTS[1].objectValues()):
            if REQUEST['AUTHENTICATED_USER'].allowed(
                        self.manage_FTPlist,
                        self.manage_FTPlist.__roles__):
                mode=mode | 0770
            if nobody.allowed(
                        self.manage_FTPlist,
                        self.manage_FTPlist.__roles__):
                mode=mode | 0007
        mtime=self.bobobase_modification_time().timeTime()
        return marshal.dumps((mode,0,0,1,0,0,0,mtime,mtime,mtime))


class PUTer(Acquisition.Explicit):
    """Class to support the HTTP PUT protocol."""

    def __init__(self, parent, id):
        self.id=id
        self.__parent__=parent
        self.__roles__ =parent.PUT__roles__
        
    def PUT(self, REQUEST, RESPONSE):
        """Adds a document, image or file to the folder when a PUT
        request is received."""
        name=self.id
        type=REQUEST.get_header('content-type', None)
        body=REQUEST.get('BODY', '')
        if type is None:
            type, enc=mimetypes.guess_type(name)
        if type is None:
            if content_types.find_binary(body) >= 0:
                type='application/octet-stream'
            else: type=content_types.text_type(body)
        type=lower(type)
        if type in ('text/html', 'text/xml', 'text/plain'):
            self.__parent__.manage_addDTMLDocument(name, '', body)
        elif type[:6]=='image/':
            ob=Image(name, '', body, content_type=type)
            self.__parent__._setObject(name, ob)
        else:
            ob=File(name, '', body, content_type=type)
            self.__parent__._setObject(name, ob)
        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE

    def __str__(self):
        return self.id






def subclass(c,super):
    if c is super: return 1
    try:
        for base in c.__bases__:
            if subclass(base,super): return 1
    except: pass
    return 0
