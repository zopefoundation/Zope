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
"""Image object"""

__version__='$Revision: 1.53 $'[11:-2]

import Globals, string, struct, mimetypes, content_types
from Globals import HTMLFile, MessageDialog
from PropertyManager import PropertyManager
from AccessControl.Role import RoleManager
from SimpleItem import Item_w__name__
from Globals import Persistent
from Acquisition import Implicit
from DateTime import DateTime


manage_addFileForm=HTMLFile('imageAdd', globals(),Kind='File',kind='file')
def manage_addFile(self,id,file,title='',precondition='',REQUEST=None):
    """Add a new File object.

    Creates a new File object 'id' with the contents of 'file'"""

    id, title = cookId(id, title, file)
    self._setObject(id, File(id,title,file,precondition))
    if REQUEST is not None: return self.manage_main(self,REQUEST)


class File(Persistent,Implicit,PropertyManager,
           RoleManager,Item_w__name__):
    """A File object is a content object for arbitrary files."""
    
    meta_type='File'
    icon='p_/file'
    precondition=''

    manage_editForm  =HTMLFile('fileEdit',globals(),Kind='File',kind='file')
    manage_uploadForm=HTMLFile('imageUpload',globals(),Kind='File',kind='file')
    manage=manage_main=manage_editForm

    manage_options=({'label':'Edit', 'action':'manage_main'},
                    {'label':'Upload', 'action':'manage_uploadForm'},
                    {'label':'Properties', 'action':'manage_propertiesForm'},
                    {'label':'View', 'action':''},
                    {'label':'Security', 'action':'manage_access'},
                   )

    __ac_permissions__=(
    ('View management screens', ['manage','manage_tabs','manage_uploadForm']),
    ('Change permissions', ['manage_access']),
    ('Change Images and Files', ['manage_edit','manage_upload','PUT']),
    ('View',
     ['index_html','view_image_or_file','getSize','getContentType', '']),
    ('Manage properties', ('manage_addProperty',
                           'manage_editProperties',
                           'manage_delProperties',
                           'manage_changeProperties',)),
    ('FTP access', ('manage_FTPstat','manage_FTPget','manage_FTPlist')),
    )
   

    _properties=({'id':'title', 'type': 'string'},
                 {'id':'content_type', 'type':'string'},
                 )

    def __init__(self, id, title, file, content_type='', precondition=''):
        self.__name__=id
        self.title=title
        self.precondition=precondition
        headers=hasattr(file, 'headers') and file.headers or None
        if (headers is None) and (not content_type):
            raise 'Bad Request', 'No content type specified.'
        if headers and headers.has_key('content-type'):
            content_type=headers['content-type']
        if not content_type:
            raise 'Bad Request', 'No content type specified.'
        data=(headers is None) and file or file.read()
        self.update_data(data, content_type)

    def id(self):
        return self.__name__

    def index_html(self, REQUEST, RESPONSE):
        """
        The default view of the contents of a File or Image.

        Returns the contents of the file or image.  Also, sets the
        Content-Type HTTP header to the objects content type.
        """

        if self.precondition and hasattr(self,self.precondition):
            # Grab whatever precondition was defined and then 
            # execute it.  The precondition will raise an exception 
            # if something violates its terms.
            c=getattr(self,self.precondition)
            if hasattr(c,'isDocTemp') and c.isDocTemp:
                c(REQUEST['PARENTS'][1],REQUEST)
            else:
                c()
        RESPONSE['content-type'] =self.content_type
        return self.data

    def view_image_or_file(self, URL1):
        """
        The default view of the contents of the File or Image.
        """
        raise 'Redirect', URL1

    def update_data(self, data, content_type=None):
        if content_type is not None:
            self.content_type=content_type
        self.data=Pdata(data)
        self.size=len(data)

    def manage_edit(self,title,content_type,precondition='',REQUEST=None):
        """
        Changes the title and content type attributes of the File or Image.
        """
        self.title=title
        self.content_type=content_type
        if precondition: self.precondition=precondition
        elif self.precondition: del self.precondition
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    def manage_upload(self,file='',REQUEST=None):
        """
        Replaces the current contents of the File or Image object with file.

        The file or images contents are replaced with the contents of 'file'.
        """
        if file.headers.has_key('content-type'):
            content_type=file.headers['content-type']
        else: content_type=None
        self.update_data(file.read(), content_type)
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    HEAD__roles__=None
    def HEAD(self, REQUEST, RESPONSE):
        """ """
        RESPONSE['content-type'] =self.content_type
        RESPONSE['content-length']=self.getSize()
        return ''

    def PUT(self, REQUEST, RESPONSE):
        """Handle HTTP PUT requests"""
        type=REQUEST.get_header('content-type', None)
        body=REQUEST.get('BODY', '')
        if type is None:
            type, enc=mimetypes.guess_type(self.id())
        if type is None:
            if content_types.find_binary(body) >= 0:
                type='application/octet-stream'
            else: type=content_types.text_type(body)
        type=string.lower(type)
        self.update_data(body, type)
        RESPONSE.setStatus(204)
        return RESPONSE
    
    def getSize(self):
        """Get the size of a file or image.

        Returns the size of the file or image.
        """
        return len(self.data)

    def getContentType(self):
        """Get the content type of a file or image.

        Returns the content type (MIME type) of a file or image.
        """
        return self.content_type

    def size(self):    return len(self.data)
    def __str__(self): return str(self.data)
    def __len__(self): return 1

    def manage_FTPget(self):
        "Get data for FTP download"
        return self.data



manage_addImageForm=HTMLFile('imageAdd',globals(),Kind='Image',kind='image')
def manage_addImage(self,id,file,title='',REQUEST=None):
    """
    Add a new Image object.

    Creates a new Image object 'id' with the contents of 'file'.
    """
    id, title = cookId(id, title, file)
    self._setObject(id, Image(id,title,file))
    if REQUEST is not None: return self.manage_main(self,REQUEST)

class Image(File):
    """Principia object for *Images*, can be GIF, PNG or JPEG.  Has the
    same methods as File objects.  Images also have a string representation
    that renders an HTML 'IMG' tag.
    """
    meta_type='Image'
    icon='p_/image'
    height=0
    width=0

    _properties=({'id':'title', 'type': 'string'},
                 {'id':'content_type', 'type':'string'},
                 {'id':'height', 'type':'int'},
                 {'id':'width', 'type':'int'},
                 )
    
    manage_options=({'label':'Edit', 'action':'manage_main'},
                    {'label':'Upload', 'action':'manage_uploadForm'},
                    {'label':'Properties', 'action':'manage_propertiesForm'},
                    {'label':'View', 'action':'view_image_or_file'},
                    {'label':'Security', 'action':'manage_access'},
                   )

    manage_editForm  =HTMLFile('imageEdit',globals(),Kind='Image',kind='image')
    view_image_or_file =HTMLFile('imageView',globals())
    manage_uploadForm=HTMLFile('imageUpload',globals(),Kind='Image',
                               kind='image')
    manage=manage_main=manage_editForm

    def update_data(self, data, content_type=None):
        if content_type is not None:
            self.content_type=content_type
        self.data=Pdata(data)
        self.size=len(data)
        # handle GIFs   
        if (self.size >= 10) and self.data[:6] in ('GIF87a', 'GIF89a'):
            w, h = struct.unpack("<HH", self.data[6:10])
            self.width=str(int(w))
            self.height=str(int(h))
        # handle PNGs
        if (self.size >= 16) and (self.data[:8] == '\x89PNG\r\n\x1a\n'):
            w, h = struct.unpack(">LL", self.data[8:16])
            self.width=str(int(w))
            self.height=str(int(h))

    def __str__(self):
        width=self.width and ('width="%s" ' % self.width) or ''
        height=self.height and ('height="%s" ' % self.height) or ''
        return '<img src="%s" %s%salt="%s">' % (
            self.absolute_url(), width, height, self.title_or_id()
            )



def cookId(id, title, file):
    if not id and hasattr(file,'filename'):
        filename=file.filename
        title=title or filename
        id=filename[max(string.rfind(filename, '/'),
                        string.rfind(filename, '\\'),
                        string.rfind(filename, ':'),
                        )+1:]                  
    return id, title

class Pdata(Persistent, Implicit):
    # Wrapper for possibly large data
    def __init__(self, data):
        self.data=data

    def __getslice__(self, i, j):
        return self.data[i:j]

    def __str__(self):
        return self.data

    def __len__(self):
        return len(self.data)

