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
"""Image object"""

__version__='$Revision: 1.125 $'[11:-2]

import Globals, string, struct, content_types
from OFS.content_types import guess_content_type
from Globals import DTMLFile, MessageDialog
from PropertyManager import PropertyManager
from AccessControl.Role import RoleManager
from webdav.common import rfc1123_date
from webdav.Lockable import ResourceLockedError
from webdav.WriteLockInterface import WriteLockInterface
from SimpleItem import Item_w__name__
from cStringIO import StringIO
from Globals import Persistent
from Acquisition import Implicit
from DateTime import DateTime
from Cache import Cacheable


StringType=type('')

manage_addFileForm=DTMLFile('dtml/imageAdd', globals(),Kind='File',kind='file')
def manage_addFile(self,id,file='',title='',precondition='', content_type='',
                   REQUEST=None):
    """Add a new File object.

    Creates a new File object 'id' with the contents of 'file'"""

    id=str(id)
    title=str(title)
    content_type=str(content_type)
    precondition=str(precondition)
    
    id, title = cookId(id, title, file)

    self=self.this()

    # First, we create the file without data:
    self._setObject(id, File(id,title,'',content_type, precondition))

    # Now we "upload" the data.  By doing this in two steps, we
    # can use a database trick to make the upload more efficient.
    self._getOb(id).manage_upload(file)
    if content_type:
        self._getOb(id).content_type=content_type

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


class File(Persistent, Implicit, PropertyManager,
           RoleManager, Item_w__name__, Cacheable):
    """A File object is a content object for arbitrary files."""
    
    __implements__ = (WriteLockInterface,)
    meta_type='File'

    
    precondition=''
    size=None

    manage_editForm  =DTMLFile('dtml/fileEdit',globals(),
                               Kind='File',kind='file')

    manage=manage_main=manage_editForm
    manage_uploadForm=manage_editForm
    
    manage_options=(
        (
        {'label':'Edit', 'action':'manage_main',
         'help':('OFSP','File_Edit.stx')},
        {'label':'View', 'action':'',
         'help':('OFSP','File_View.stx')},
        )
        + PropertyManager.manage_options
        + RoleManager.manage_options
        + Item_w__name__.manage_options
        + Cacheable.manage_options
        )


    __ac_permissions__=(
        ('View management screens',
         ('manage', 'manage_main',)),
        ('Change Images and Files',
         ('manage_edit','manage_upload','PUT')),
        ('View',
         ('index_html', 'view_image_or_file', 'get_size',
          'getContentType', '')),
        ('FTP access',
         ('manage_FTPstat','manage_FTPget','manage_FTPlist')),
        ('Delete objects',
         ('DELETE',)),
        )
   

    _properties=({'id':'title', 'type': 'string'},
                 {'id':'content_type', 'type':'string'},
                 )

    def __init__(self, id, title, file, content_type='', precondition=''):
        self.__name__=id
        self.title=title
        self.precondition=precondition
       
        data, size = self._read_data(file)
        content_type=self._get_content_type(file, data, id, content_type)
        self.update_data(data, content_type, size)

    def id(self):
        return self.__name__

    def index_html(self, REQUEST, RESPONSE):
        """
        The default view of the contents of a File or Image.

        Returns the contents of the file or image.  Also, sets the
        Content-Type HTTP header to the objects content type.
        """
        # HTTP If-Modified-Since header handling.
        header=REQUEST.get_header('If-Modified-Since', None)
        if header is not None:
            header=string.split(header, ';')[0]
            # Some proxies seem to send invalid date strings for this
            # header. If the date string is not valid, we ignore it
            # rather than raise an error to be generally consistent
            # with common servers such as Apache (which can usually
            # understand the screwy date string as a lucky side effect
            # of the way they parse it).
            try:    mod_since=long(DateTime(header).timeTime())
            except: mod_since=None
            if mod_since is not None:
                if self._p_mtime:
                    last_mod = long(self._p_mtime)
                else:
                    last_mod = long(0)
                if last_mod > 0 and last_mod <= mod_since:
                    RESPONSE.setStatus(304)
                    return ''

        if self.precondition and hasattr(self,self.precondition):
            # Grab whatever precondition was defined and then 
            # execute it.  The precondition will raise an exception 
            # if something violates its terms.
            c=getattr(self,self.precondition)
            if hasattr(c,'isDocTemp') and c.isDocTemp:
                c(REQUEST['PARENTS'][1],REQUEST)
            else:
                c()
        RESPONSE.setHeader('Last-Modified', rfc1123_date(self._p_mtime))
        RESPONSE.setHeader('Content-Type', self.content_type)
        RESPONSE.setHeader('Content-Length', self.size)

        # Don't cache the data itself, but provide an opportunity
        # for a cache manager to set response headers.
        self.ZCacheable_set(None)

        data=self.data
        if type(data) is type(''): return data

        while data is not None:
            RESPONSE.write(data.data)
            data=data.next

        return ''

    def view_image_or_file(self, URL1):
        """
        The default view of the contents of the File or Image.
        """
        raise 'Redirect', URL1

    # private
    update_data__roles__=()
    def update_data(self, data, content_type=None, size=None):
        if content_type is not None: self.content_type=content_type
        if size is None: size=len(data)
        self.size=size
        self.data=data
        self.ZCacheable_invalidate()

    def manage_edit(self, title, content_type, precondition='', REQUEST=None):
        """
        Changes the title and content type attributes of the File or Image.
        """
        if self.wl_isLocked():
            raise ResourceLockedError, "File is locked via WebDAV"

        self.title=str(title)
        self.content_type=str(content_type)
        if precondition: self.precondition=str(precondition)
        elif self.precondition: del self.precondition
        self.ZCacheable_invalidate()
        if REQUEST:
            message="Saved changes."
            return self.manage_main(self,REQUEST,manage_tabs_message=message)

    def manage_upload(self,file='',REQUEST=None):
        """
        Replaces the current contents of the File or Image object with file.

        The file or images contents are replaced with the contents of 'file'.
        """
        if self.wl_isLocked():
            raise ResourceLockedError, "File is locked via WebDAV"

        data, size = self._read_data(file)
        content_type=self._get_content_type(file, data, self.__name__,
                                            'application/octet-stream')
        self.update_data(data, content_type, size)

        if REQUEST:
            message="Saved changes."
            return self.manage_main(self,REQUEST,manage_tabs_message=message)
        
    def _get_content_type(self, file, body, id, content_type=None):
        headers=getattr(file, 'headers', None)
        if headers and headers.has_key('content-type'):
            content_type=headers['content-type']
        else:
            if type(body) is not type(''): body=body.data
            content_type, enc=guess_content_type(
                getattr(file, 'filename',id), body, content_type)
        return content_type

    def _read_data(self, file):
        
        n=1 << 16
        
        if type(file) is StringType:
            size=len(file)
            if size < n: return file, size
            return Pdata(file), size

        if hasattr(file, '__class__') and file.__class__ is Pdata:
            size=len(file)
            return file, size

        seek=file.seek
        read=file.read
        
        seek(0,2)
        size=end=file.tell()

        if size <= 2*n:
            seek(0)
            if size < n: return read(size), size
            return Pdata(read(size)), size

        # Make sure we have an _p_jar, even if we are a new object, by
        # doing a sub-transaction commit.
        get_transaction().commit(1)
        
        jar=self._p_jar
        
        if jar is None:
            # Ugh
            seek(0)
            return Pdata(read(size)), size

        # Now we're going to build a linked list from back
        # to front to minimize the number of database updates
        # and to allow us to get things out of memory as soon as
        # possible.
        next=None
        while end > 0:
            pos=end-n
            if pos < n: pos=0 # we always want at least n bytes
            seek(pos)
            data=Pdata(read(end-pos))
            
            # Woooop Woooop Woooop! This is a trick.
            # We stuff the data directly into our jar to reduce the
            # number of updates necessary.
            data._p_jar=jar

            # This is needed and has side benefit of getting
            # the thing registered:
            data.next=next
            
            # Now make it get saved in a sub-transaction!
            get_transaction().commit(1)

            # Now make it a ghost to free the memory.  We
            # don't need it anymore!
            data._p_changed=None
            
            next=data
            end=pos
        
        return next, size

    def PUT(self, REQUEST, RESPONSE):
        """Handle HTTP PUT requests"""
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        type=REQUEST.get_header('content-type', None)

        file=REQUEST['BODYFILE']
        
        data, size = self._read_data(file)
        content_type=self._get_content_type(file, data, self.__name__,
                                            type or self.content_type)
        self.update_data(data, content_type, size)

        RESPONSE.setStatus(204)
        return RESPONSE
    
    def get_size(self):
        """Get the size of a file or image.

        Returns the size of the file or image.
        """
        size=self.size
        if size is None: size=len(self.data)
        return size

    # deprecated; use get_size!
    getSize=get_size

    def getContentType(self):
        """Get the content type of a file or image.

        Returns the content type (MIME type) of a file or image.
        """
        return self.content_type


    def __str__(self): return str(self.data)
    def __len__(self): return 1
    
    manage_FTPget=index_html


manage_addImageForm=DTMLFile('dtml/imageAdd',globals(),
                             Kind='Image',kind='image')
def manage_addImage(self, id, file, title='', precondition='', content_type='',
                    REQUEST=None):
    """
    Add a new Image object.

    Creates a new Image object 'id' with the contents of 'file'.
    """

    id=str(id)
    title=str(title)
    content_type=str(content_type)
    precondition=str(precondition)

    id, title = cookId(id, title, file)

    self=self.this()

    # First, we create the image without data:
    self._setObject(id, Image(id,title,'',content_type, precondition))
        
    # Now we "upload" the data.  By doing this in two steps, we
    # can use a database trick to make the upload more efficient.
    self._getOb(id).manage_upload(file)
    if content_type:
        self._getOb(id).content_type=content_type
    
    if REQUEST is not None:
        try:    url=self.DestinationURL()
        except: url=REQUEST['URL1']
        REQUEST.RESPONSE.redirect('%s/manage_main' % url)
    return id


def getImageInfo(data):
    data = str(data)
    size = len(data)
    height = -1
    width = -1
    content_type = ''

    # handle GIFs   
    if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
        # Check to see if content_type is correct
        content_type = 'image/gif'
        w, h = struct.unpack("<HH", data[6:10])
        width = int(w)
        height = int(h)

    # See PNG v1.2 spec (http://www.cdrom.com/pub/png/spec/)
    # Bytes 0-7 are below, 4-byte chunk length, then 'IHDR'
    # and finally the 4-byte width, height
    elif ((size >= 24) and (data[:8] == '\211PNG\r\n\032\n')
          and (data[12:16] == 'IHDR')):
        content_type = 'image/png'
        w, h = struct.unpack(">LL", data[16:24])
        width = int(w)
        height = int(h)
            
    # Maybe this is for an older PNG version.
    elif (size >= 16) and (data[:8] == '\211PNG\r\n\032\n'):
        # Check to see if we have the right content type
        content_type = 'image/png'
        w, h = struct.unpack(">LL", data[8:16])
        width = int(w)
        height = int(h)

    # handle JPEGs
    elif (size >= 2) and (data[:2] == '\377\330'):
        content_type = 'image/jpeg'
        jpeg = StringIO(data)
        jpeg.read(2)
        b = jpeg.read(1)
        try:
            while (b and ord(b) != 0xDA):
                while (ord(b) != 0xFF): b = jpeg.read(1)
                while (ord(b) == 0xFF): b = jpeg.read(1)
                if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                    jpeg.read(3)
                    h, w = struct.unpack(">HH", jpeg.read(4))
                    break
                else:
                    jpeg.read(int(struct.unpack(">H", jpeg.read(2))[0])-2)
                b = jpeg.read(1)
            width = int(w)
            height = int(h)
        except: pass

    return content_type, width, height


class Image(File):
    """Image objects can be GIF, PNG or JPEG and have the same methods
    as File objects.  Images also have a string representation that
    renders an HTML 'IMG' tag.
    """
    __implements__ = (WriteLockInterface,)
    meta_type='Image'

    
    height=''
    width=''

    __ac_permissions__=(
        ('View management screens',
         ('manage', 'manage_main',)),
        ('Change Images and Files',
         ('manage_edit','manage_upload','PUT')),
        ('View',
         ('index_html', 'tag', 'view_image_or_file', 'get_size',
          'getContentType', '')),
        ('FTP access',
         ('manage_FTPstat','manage_FTPget','manage_FTPlist')),
        ('Delete objects',
         ('DELETE',)),
        )

    _properties=({'id':'title', 'type': 'string'},
                 {'id':'content_type', 'type':'string'},
                 {'id':'height', 'type':'string'},
                 {'id':'width', 'type':'string'},
                 )

    manage_options=(
        ({'label':'Edit', 'action':'manage_main',
         'help':('OFSP','Image_Edit.stx')},
         {'label':'View', 'action':'view_image_or_file',
         'help':('OFSP','Image_View.stx')},)
        + PropertyManager.manage_options
        + RoleManager.manage_options
        + Item_w__name__.manage_options
        + Cacheable.manage_options
        )

    manage_editForm  =DTMLFile('dtml/imageEdit',globals(),
                               Kind='Image',kind='image')
    view_image_or_file =DTMLFile('dtml/imageView',globals())

    manage=manage_main=manage_editForm
    manage_uploadForm=manage_editForm
    
    # private
    update_data__roles__=()
    def update_data(self, data, content_type=None, size=None):
        if size is None: size=len(data)

        self.size=size
        self.data=data

        ct, width, height = getImageInfo(data)
        if ct:
            content_type = ct
        if width >= 0 and height >= 0:
            self.width = width
            self.height = height

        # Now we should have the correct content type, or still None
        if content_type is not None: self.content_type = content_type

        self.ZCacheable_invalidate()


    def __str__(self):
        return self.tag()

    def tag(self, height=None, width=None, alt=None,
            scale=0, xscale=0, yscale=0, **args):
        """
        Generate an HTML IMG tag for this image, with customization.
        Arguments to self.tag() can be any valid attributes of an IMG tag.
        'src' will always be an absolute pathname, to prevent redundant
        downloading of images. Defaults are applied intelligently for
        'height', 'width', and 'alt'. If specified, the 'scale', 'xscale',
        and 'yscale' keyword arguments will be used to automatically adjust
        the output height and width values of the image tag.
        """
        if height is None: height=self.height
        if width is None:  width=self.width

        # Auto-scaling support
        xdelta = xscale or scale
        ydelta = yscale or scale

        if xdelta and width:
            width = str(int(width) * xdelta)
        if ydelta and height:
            height = str(int(height) * ydelta)

        result='<img src="%s"' % (self.absolute_url())

        if alt is None:
            alt=getattr(self, 'title', '')
        result = '%s alt="%s"' % (result, alt)

        if height:
            result = '%s height="%s"' % (result, height)

        if width:
            result = '%s width="%s"' % (result, width)

        if not 'border' in map(string.lower, args.keys()):
            result = '%s border="0"' % result

        for key in args.keys():
            value = args.get(key)
            result = '%s %s="%s"' % (result, key, value)

        return '%s />' % result


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

    next=None
    
    def __init__(self, data):
        self.data=data

    def __getslice__(self, i, j):
        return self.data[i:j]

    def __len__(self):
        data = str(self)
        return len(data)

    def __str__(self):
        next=self.next
        if next is None: return self.data

        r=[self.data]
        while next is not None:
            self=next
            r.append(self.data)
            next=self.next
        
        return string.join(r,'')









