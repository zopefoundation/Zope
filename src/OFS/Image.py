##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Image object
"""

from cgi import escape
from cStringIO import StringIO
from mimetools import choose_boundary
import struct

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import change_images_and_files
from AccessControl.Permissions import view_management_screens
from AccessControl.Permissions import view as View
from AccessControl.Permissions import ftp_access
from AccessControl.Permissions import delete_objects
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from App.special_dtml import DTMLFile
from DateTime.DateTime import DateTime
from Persistence import Persistent
from webdav.common import rfc1123_date
from webdav.interfaces import IWriteLock
from webdav.Lockable import ResourceLockedError
from ZPublisher import HTTPRangeSupport
from ZPublisher.HTTPRequest import FileUpload
from zExceptions import Redirect
from zope.contenttype import guess_content_type
from zope.interface import implementedBy
from zope.interface import implements

from OFS.Cache import Cacheable
from OFS.PropertyManager import PropertyManager
from OFS.role import RoleManager
from OFS.SimpleItem import Item_w__name__

from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.lifecycleevent import ObjectCreatedEvent

manage_addFileForm = DTMLFile('dtml/imageAdd',
                              globals(),
                              Kind='File',
                              kind='file',
                             )
def manage_addFile(self, id, file='', title='', precondition='',
                   content_type='', REQUEST=None):
    """Add a new File object.

    Creates a new File object 'id' with the contents of 'file'"""

    id = str(id)
    title = str(title)
    content_type = str(content_type)
    precondition = str(precondition)

    id, title = cookId(id, title, file)
    
    self=self.this()

    # First, we create the file without data:
    self._setObject(id, File(id,title,'',content_type, precondition))
    
    newFile = self._getOb(id)
    
    # Now we "upload" the data.  By doing this in two steps, we
    # can use a database trick to make the upload more efficient.
    if file:
        newFile.manage_upload(file)
    if content_type:
        newFile.content_type=content_type
    
    notify(ObjectCreatedEvent(newFile))
    
    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


class File(Persistent, Implicit, PropertyManager,
           RoleManager, Item_w__name__, Cacheable):
    """A File object is a content object for arbitrary files."""

    implements(implementedBy(Persistent),
               implementedBy(Implicit),
               implementedBy(PropertyManager),
               implementedBy(RoleManager),
               implementedBy(Item_w__name__),
               implementedBy(Cacheable),
               IWriteLock,
               HTTPRangeSupport.HTTPRangeInterface,
              )
    meta_type='File'

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    precondition=''
    size=None

    manage_editForm  =DTMLFile('dtml/fileEdit',globals(),
                               Kind='File',kind='file')
    manage_editForm._setName('manage_editForm')

    security.declareProtected(view_management_screens, 'manage')
    security.declareProtected(view_management_screens, 'manage_main')
    manage=manage_main=manage_editForm
    manage_uploadForm=manage_editForm

    manage_options=(
        (
        {'label': 'Edit', 'action': 'manage_main'},
        {'label': 'View', 'action': ''},
        )
        + PropertyManager.manage_options
        + RoleManager.manage_options
        + Item_w__name__.manage_options
        + Cacheable.manage_options
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

    def _if_modified_since_request_handler(self, REQUEST, RESPONSE):
        # HTTP If-Modified-Since header handling: return True if
        # we can handle this request by returning a 304 response
        header=REQUEST.get_header('If-Modified-Since', None)
        if header is not None:
            header=header.split( ';')[0]
            # Some proxies seem to send invalid date strings for this
            # header. If the date string is not valid, we ignore it
            # rather than raise an error to be generally consistent
            # with common servers such as Apache (which can usually
            # understand the screwy date string as a lucky side effect
            # of the way they parse it).
            # This happens to be what RFC2616 tells us to do in the face of an
            # invalid date.
            try:    mod_since=long(DateTime(header).timeTime())
            except: mod_since=None
            if mod_since is not None:
                if self._p_mtime:
                    last_mod = long(self._p_mtime)
                else:
                    last_mod = long(0)
                if last_mod > 0 and last_mod <= mod_since:
                    RESPONSE.setHeader('Last-Modified',
                                       rfc1123_date(self._p_mtime))
                    RESPONSE.setHeader('Content-Type', self.content_type)
                    RESPONSE.setHeader('Accept-Ranges', 'bytes')
                    RESPONSE.setStatus(304)
                    return True

    def _range_request_handler(self, REQUEST, RESPONSE):
        # HTTP Range header handling: return True if we've served a range
        # chunk out of our data.
        range = REQUEST.get_header('Range', None)
        request_range = REQUEST.get_header('Request-Range', None)
        if request_range is not None:
            # Netscape 2 through 4 and MSIE 3 implement a draft version
            # Later on, we need to serve a different mime-type as well.
            range = request_range
        if_range = REQUEST.get_header('If-Range', None)
        if range is not None:
            ranges = HTTPRangeSupport.parseRange(range)

            if if_range is not None:
                # Only send ranges if the data isn't modified, otherwise send
                # the whole object. Support both ETags and Last-Modified dates!
                if len(if_range) > 1 and if_range[:2] == 'ts':
                    # ETag:
                    if if_range != self.http__etag():
                        # Modified, so send a normal response. We delete
                        # the ranges, which causes us to skip to the 200
                        # response.
                        ranges = None
                else:
                    # Date
                    date = if_range.split( ';')[0]
                    try: mod_since=long(DateTime(date).timeTime())
                    except: mod_since=None
                    if mod_since is not None:
                        if self._p_mtime:
                            last_mod = long(self._p_mtime)
                        else:
                            last_mod = long(0)
                        if last_mod > mod_since:
                            # Modified, so send a normal response. We delete
                            # the ranges, which causes us to skip to the 200
                            # response.
                            ranges = None

            if ranges:
                # Search for satisfiable ranges.
                satisfiable = 0
                for start, end in ranges:
                    if start < self.size:
                        satisfiable = 1
                        break

                if not satisfiable:
                    RESPONSE.setHeader('Content-Range',
                        'bytes */%d' % self.size)
                    RESPONSE.setHeader('Accept-Ranges', 'bytes')
                    RESPONSE.setHeader('Last-Modified',
                        rfc1123_date(self._p_mtime))
                    RESPONSE.setHeader('Content-Type', self.content_type)
                    RESPONSE.setHeader('Content-Length', self.size)
                    RESPONSE.setStatus(416)
                    return True

                ranges = HTTPRangeSupport.expandRanges(ranges, self.size)

                if len(ranges) == 1:
                    # Easy case, set extra header and return partial set.
                    start, end = ranges[0]
                    size = end - start

                    RESPONSE.setHeader('Last-Modified',
                        rfc1123_date(self._p_mtime))
                    RESPONSE.setHeader('Content-Type', self.content_type)
                    RESPONSE.setHeader('Content-Length', size)
                    RESPONSE.setHeader('Accept-Ranges', 'bytes')
                    RESPONSE.setHeader('Content-Range',
                        'bytes %d-%d/%d' % (start, end - 1, self.size))
                    RESPONSE.setStatus(206) # Partial content

                    data = self.data
                    if isinstance(data, str):
                        RESPONSE.write(data[start:end])
                        return True

                    # Linked Pdata objects. Urgh.
                    pos = 0
                    while data is not None:
                        l = len(data.data)
                        pos = pos + l
                        if pos > start:
                            # We are within the range
                            lstart = l - (pos - start)

                            if lstart < 0: lstart = 0

                            # find the endpoint
                            if end <= pos:
                                lend = l - (pos - end)

                                # Send and end transmission
                                RESPONSE.write(data[lstart:lend])
                                break

                            # Not yet at the end, transmit what we have.
                            RESPONSE.write(data[lstart:])

                        data = data.next

                    return True

                else:
                    boundary = choose_boundary()

                    # Calculate the content length
                    size = (8 + len(boundary) + # End marker length
                        len(ranges) * (         # Constant lenght per set
                            49 + len(boundary) + len(self.content_type) +
                            len('%d' % self.size)))
                    for start, end in ranges:
                        # Variable length per set
                        size = (size + len('%d%d' % (start, end - 1)) +
                            end - start)


                    # Some clients implement an earlier draft of the spec, they
                    # will only accept x-byteranges.
                    draftprefix = (request_range is not None) and 'x-' or ''

                    RESPONSE.setHeader('Content-Length', size)
                    RESPONSE.setHeader('Accept-Ranges', 'bytes')
                    RESPONSE.setHeader('Last-Modified',
                        rfc1123_date(self._p_mtime))
                    RESPONSE.setHeader('Content-Type',
                        'multipart/%sbyteranges; boundary=%s' % (
                            draftprefix, boundary))
                    RESPONSE.setStatus(206) # Partial content

                    data = self.data
                    # The Pdata map allows us to jump into the Pdata chain
                    # arbitrarily during out-of-order range searching.
                    pdata_map = {}
                    pdata_map[0] = data

                    for start, end in ranges:
                        RESPONSE.write('\r\n--%s\r\n' % boundary)
                        RESPONSE.write('Content-Type: %s\r\n' %
                            self.content_type)
                        RESPONSE.write(
                            'Content-Range: bytes %d-%d/%d\r\n\r\n' % (
                                start, end - 1, self.size))

                        if isinstance(data, str):
                            RESPONSE.write(data[start:end])

                        else:
                            # Yippee. Linked Pdata objects. The following
                            # calculations allow us to fast-forward through the
                            # Pdata chain without a lot of dereferencing if we
                            # did the work already.
                            first_size = len(pdata_map[0].data)
                            if start < first_size:
                                closest_pos = 0
                            else:
                                closest_pos = (
                                    ((start - first_size) >> 16 << 16) +
                                    first_size)
                            pos = min(closest_pos, max(pdata_map.keys()))
                            data = pdata_map[pos]

                            while data is not None:
                                l = len(data.data)
                                pos = pos + l
                                if pos > start:
                                    # We are within the range
                                    lstart = l - (pos - start)

                                    if lstart < 0: lstart = 0

                                    # find the endpoint
                                    if end <= pos:
                                        lend = l - (pos - end)

                                        # Send and loop to next range
                                        RESPONSE.write(data[lstart:lend])
                                        break

                                    # Not yet at the end, transmit what we have.
                                    RESPONSE.write(data[lstart:])

                                data = data.next
                                # Store a reference to a Pdata chain link so we
                                # don't have to deref during this request again.
                                pdata_map[pos] = data

                    # Do not keep the link references around.
                    del pdata_map

                    RESPONSE.write('\r\n--%s--\r\n' % boundary)
                    return True

    security.declareProtected(View, 'index_html')
    def index_html(self, REQUEST, RESPONSE):
        """
        The default view of the contents of a File or Image.

        Returns the contents of the file or image.  Also, sets the
        Content-Type HTTP header to the objects content type.
        """

        if self._if_modified_since_request_handler(REQUEST, RESPONSE):
            # we were able to handle this by returning a 304
            # unfortunately, because the HTTP cache manager uses the cache
            # API, and because 304 responses are required to carry the Expires
            # header for HTTP/1.1, we need to call ZCacheable_set here.
            # This is nonsensical for caches other than the HTTP cache manager
            # unfortunately.
            self.ZCacheable_set(None)
            return ''

        if self.precondition and hasattr(self, str(self.precondition)):
            # Grab whatever precondition was defined and then
            # execute it.  The precondition will raise an exception
            # if something violates its terms.
            c=getattr(self, str(self.precondition))
            if hasattr(c,'isDocTemp') and c.isDocTemp:
                c(REQUEST['PARENTS'][1],REQUEST)
            else:
                c()

        if self._range_request_handler(REQUEST, RESPONSE):
            # we served a chunk of content in response to a range request.
            return ''

        RESPONSE.setHeader('Last-Modified', rfc1123_date(self._p_mtime))
        RESPONSE.setHeader('Content-Type', self.content_type)
        RESPONSE.setHeader('Content-Length', self.size)
        RESPONSE.setHeader('Accept-Ranges', 'bytes')

        if self.ZCacheable_isCachingEnabled():
            result = self.ZCacheable_get(default=None)
            if result is not None:
                # We will always get None from RAMCacheManager and HTTP
                # Accelerated Cache Manager but we will get
                # something implementing the IStreamIterator interface
                # from a "FileCacheManager"
                return result

        self.ZCacheable_set(None)

        data=self.data
        if isinstance(data, str):
            RESPONSE.setBase(None)
            return data

        while data is not None:
            RESPONSE.write(data.data)
            data=data.next

        return ''

    security.declareProtected(View, 'view_image_or_file')
    def view_image_or_file(self, URL1):
        """
        The default view of the contents of the File or Image.
        """
        raise Redirect, URL1

    security.declareProtected(View, 'PrincipiaSearchSource')
    def PrincipiaSearchSource(self):
        """ Allow file objects to be searched.
        """
        if self.content_type.startswith('text/'):
            return str(self.data)
        return ''

    security.declarePrivate('update_data')
    def update_data(self, data, content_type=None, size=None):
        if isinstance(data, unicode):
            raise TypeError('Data can only be str or file-like.  '
                            'Unicode objects are expressly forbidden.')

        if content_type is not None: self.content_type=content_type
        if size is None: size=len(data)
        self.size=size
        self.data=data
        self.ZCacheable_invalidate()
        self.ZCacheable_set(None)
        self.http__refreshEtag()

    security.declareProtected(change_images_and_files, 'manage_edit')
    def manage_edit(self, title, content_type, precondition='',
                    filedata=None, REQUEST=None):
        """
        Changes the title and content type attributes of the File or Image.
        """
        if self.wl_isLocked():
            raise ResourceLockedError, "File is locked via WebDAV"

        self.title=str(title)
        self.content_type=str(content_type)
        if precondition: self.precondition=str(precondition)
        elif self.precondition: del self.precondition
        if filedata is not None:
            self.update_data(filedata, content_type, len(filedata))
        else:
            self.ZCacheable_invalidate()
        
        notify(ObjectModifiedEvent(self))
        
        if REQUEST:
            message="Saved changes."
            return self.manage_main(self,REQUEST,manage_tabs_message=message)

    security.declareProtected(change_images_and_files, 'manage_upload')
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
        
        notify(ObjectModifiedEvent(self))
        
        if REQUEST:
            message="Saved changes."
            return self.manage_main(self,REQUEST,manage_tabs_message=message)

    def _get_content_type(self, file, body, id, content_type=None):
        headers=getattr(file, 'headers', None)
        if headers and 'content-type' in headers:
            content_type=headers['content-type']
        else:
            if not isinstance(body, str): body=body.data
            content_type, enc=guess_content_type(
                getattr(file, 'filename',id), body, content_type)
        return content_type

    def _read_data(self, file):
        import transaction

        n=1 << 16

        if isinstance(file, str):
            size=len(file)
            if size < n: return file, size
            # Big string: cut it into smaller chunks
            file = StringIO(file)

        if isinstance(file, FileUpload) and not file:
            raise ValueError, 'File not specified'

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
        transaction.savepoint(optimistic=True)

        if self._p_jar is None:
            # Ugh
            seek(0)
            return Pdata(read(size)), size

        # Now we're going to build a linked list from back
        # to front to minimize the number of database updates
        # and to allow us to get things out of memory as soon as
        # possible.
        next = None
        while end > 0:
            pos = end-n
            if pos < n:
                pos = 0 # we always want at least n bytes
            seek(pos)

            # Create the object and assign it a next pointer
            # in the same transaction, so that there is only
            # a single database update for it.
            data = Pdata(read(end-pos))
            self._p_jar.add(data)
            data.next = next

            # Save the object so that we can release its memory.
            transaction.savepoint(optimistic=True)
            data._p_deactivate()
            # The object should be assigned an oid and be a ghost.
            assert data._p_oid is not None
            assert data._p_state == -1

            next = data
            end = pos

        return next, size

    security.declareProtected(delete_objects, 'DELETE')

    security.declareProtected(change_images_and_files, 'PUT')
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

    security.declareProtected(View, 'get_size')
    def get_size(self):
        """Get the size of a file or image.

        Returns the size of the file or image.
        """
        size=self.size
        if size is None: size=len(self.data)
        return size

    # deprecated; use get_size!
    getSize=get_size

    security.declareProtected(View, 'getContentType')
    def getContentType(self):
        """Get the content type of a file or image.

        Returns the content type (MIME type) of a file or image.
        """
        return self.content_type


    def __str__(self): return str(self.data)
    def __len__(self): return 1

    security.declareProtected(ftp_access, 'manage_FTPstat')
    security.declareProtected(ftp_access, 'manage_FTPlist')

    security.declareProtected(ftp_access, 'manage_FTPget')
    def manage_FTPget(self):
        """Return body for ftp."""
        RESPONSE = self.REQUEST.RESPONSE

        if self.ZCacheable_isCachingEnabled():
            result = self.ZCacheable_get(default=None)
            if result is not None:
                # We will always get None from RAMCacheManager but we will get
                # something implementing the IStreamIterator interface
                # from FileCacheManager.
                # the content-length is required here by HTTPResponse, even
                # though FTP doesn't use it.
                RESPONSE.setHeader('Content-Length', self.size)
                return result

        data = self.data
        if isinstance(data, str):
            RESPONSE.setBase(None)
            return data

        while data is not None:
            RESPONSE.write(data.data)
            data = data.next

        return ''

InitializeClass(File)


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
    
    newFile = self._getOb(id)
    
    # Now we "upload" the data.  By doing this in two steps, we
    # can use a database trick to make the upload more efficient.
    if file:
        newFile.manage_upload(file)
    if content_type:
        newFile.content_type=content_type
    
    notify(ObjectCreatedEvent(newFile))
    
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
    meta_type='Image'

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    alt=''
    height=''
    width=''

    # FIXME: Redundant, already in base class
    security.declareProtected(change_images_and_files, 'manage_edit')
    security.declareProtected(change_images_and_files, 'manage_upload')
    security.declareProtected(change_images_and_files, 'PUT')
    security.declareProtected(View, 'index_html')
    security.declareProtected(View, 'get_size')
    security.declareProtected(View, 'getContentType')
    security.declareProtected(ftp_access, 'manage_FTPstat')
    security.declareProtected(ftp_access, 'manage_FTPlist')
    security.declareProtected(ftp_access, 'manage_FTPget')
    security.declareProtected(delete_objects, 'DELETE')

    _properties=({'id':'title', 'type': 'string'},
                 {'id':'alt', 'type':'string'},
                 {'id':'content_type', 'type':'string','mode':'w'},
                 {'id':'height', 'type':'string'},
                 {'id':'width', 'type':'string'},
                 )

    manage_options=(
        ({'label':'Edit', 'action':'manage_main'},
         {'label':'View', 'action':'view_image_or_file'}, )
        + PropertyManager.manage_options
        + RoleManager.manage_options
        + Item_w__name__.manage_options
        + Cacheable.manage_options
        )

    manage_editForm  =DTMLFile('dtml/imageEdit',globals(),
                               Kind='Image',kind='image')
    manage_editForm._setName('manage_editForm')

    security.declareProtected(View, 'view_image_or_file')
    view_image_or_file =DTMLFile('dtml/imageView',globals())

    security.declareProtected(view_management_screens, 'manage')
    security.declareProtected(view_management_screens, 'manage_main')
    manage=manage_main=manage_editForm
    manage_uploadForm=manage_editForm

    security.declarePrivate('update_data')
    def update_data(self, data, content_type=None, size=None):
        if isinstance(data, unicode):
            raise TypeError('Data can only be str or file-like.  '
                            'Unicode objects are expressly forbidden.')
        
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
        self.ZCacheable_set(None)
        self.http__refreshEtag()

    def __str__(self):
        return self.tag()

    security.declareProtected(View, 'tag')
    def tag(self, height=None, width=None, alt=None,
            scale=0, xscale=0, yscale=0, css_class=None, title=None, **args):
        """
        Generate an HTML IMG tag for this image, with customization.
        Arguments to self.tag() can be any valid attributes of an IMG tag.
        'src' will always be an absolute pathname, to prevent redundant
        downloading of images. Defaults are applied intelligently for
        'height', 'width', and 'alt'. If specified, the 'scale', 'xscale',
        and 'yscale' keyword arguments will be used to automatically adjust
        the output height and width values of the image tag.

        Since 'class' is a Python reserved word, it cannot be passed in
        directly in keyword arguments which is a problem if you are
        trying to use 'tag()' to include a CSS class. The tag() method
        will accept a 'css_class' argument that will be converted to
        'class' in the output tag to work around this.
        """
        if height is None: height=self.height
        if width is None:  width=self.width

        # Auto-scaling support
        xdelta = xscale or scale
        ydelta = yscale or scale

        if xdelta and width:
            width =  str(int(round(int(width) * xdelta)))
        if ydelta and height:
            height = str(int(round(int(height) * ydelta)))

        result='<img src="%s"' % (self.absolute_url())

        if alt is None:
            alt=getattr(self, 'alt', '')
        result = '%s alt="%s"' % (result, escape(alt, 1))

        if title is None:
            title=getattr(self, 'title', '')
        result = '%s title="%s"' % (result, escape(title, 1))

        if height:
            result = '%s height="%s"' % (result, height)

        if width:
            result = '%s width="%s"' % (result, width)

        # Omitting 'border' attribute (Collector #1557)
#        if not 'border' in [ x.lower() for x in  args.keys()]:
#            result = '%s border="0"' % result

        if css_class is not None:
            result = '%s class="%s"' % (result, css_class)

        for key in args.keys():
            value = args.get(key)
            if value:
                result = '%s %s="%s"' % (result, key, value)

        return '%s />' % result

InitializeClass(Image)


def cookId(id, title, file):
    if not id and hasattr(file,'filename'):
        filename=file.filename
        title=title or filename
        id=filename[max(filename.rfind('/'),
                        filename.rfind('\\'),
                        filename.rfind(':'),
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

        return ''.join(r)
