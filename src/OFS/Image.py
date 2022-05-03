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

import html
import struct
from email.generator import _make_boundary
from io import BytesIO

import ZPublisher.HTTPRequest
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import change_images_and_files  # NOQA
from AccessControl.Permissions import view as View
from AccessControl.Permissions import view_management_screens
from AccessControl.Permissions import webdav_access
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from App.special_dtml import DTMLFile
from DateTime.DateTime import DateTime
from OFS.Cache import Cacheable
from OFS.interfaces import IWriteLock
from OFS.PropertyManager import PropertyManager
from OFS.role import RoleManager
from OFS.SimpleItem import Item_w__name__
from OFS.SimpleItem import PathReprProvider
from Persistence import Persistent
from zExceptions import Redirect
from zExceptions import ResourceLockedError
from zope.contenttype import guess_content_type
from zope.datetime import rfc1123_date
from zope.event import notify
from zope.interface import implementer
from zope.lifecycleevent import ObjectCreatedEvent
from zope.lifecycleevent import ObjectModifiedEvent
from ZPublisher import HTTPRangeSupport
from ZPublisher.HTTPRequest import FileUpload


manage_addFileForm = DTMLFile(
    'dtml/imageAdd',
    globals(),
    Kind='File',
    kind='file',
)


def manage_addFile(
    self,
    id,
    file=b'',
    title='',
    precondition='',
    content_type='',
    REQUEST=None
):
    """Add a new File object.

    Creates a new File object 'id' with the contents of 'file'"""

    id = str(id)
    title = str(title)
    content_type = str(content_type)
    precondition = str(precondition)

    id, title = cookId(id, title, file)

    self = self.this()

    # First, we create the file without data:
    self._setObject(id, File(id, title, b'', content_type, precondition))

    newFile = self._getOb(id)

    # Now we "upload" the data.  By doing this in two steps, we
    # can use a database trick to make the upload more efficient.
    if file:
        newFile.manage_upload(file)
    if content_type:
        newFile.content_type = content_type

    notify(ObjectCreatedEvent(newFile))

    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(self.absolute_url() + '/manage_main')


@implementer(IWriteLock, HTTPRangeSupport.HTTPRangeInterface)
class File(
    PathReprProvider,
    Persistent,
    Implicit,
    PropertyManager,
    RoleManager,
    Item_w__name__,
    Cacheable
):
    """A File object is a content object for arbitrary files."""

    meta_type = 'File'
    zmi_icon = 'far fa-file-archive'

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    precondition = ''
    size = None

    manage_editForm = DTMLFile('dtml/fileEdit', globals(),
                               Kind='File', kind='file')
    manage_editForm._setName('manage_editForm')

    security.declareProtected(view_management_screens, 'manage')  # NOQA: D001
    security.declareProtected(view_management_screens, 'manage_main')  # NOQA: D001,E501
    manage = manage_main = manage_editForm
    manage_uploadForm = manage_editForm

    manage_options = (({'label': 'Edit', 'action': 'manage_main'},
                       {'label': 'View', 'action': ''})
                      + PropertyManager.manage_options
                      + RoleManager.manage_options
                      + Item_w__name__.manage_options
                      + Cacheable.manage_options)

    _properties = (
        {'id': 'title', 'type': 'string'},
        {'id': 'content_type', 'type': 'string'},
    )

    def __init__(self, id, title, file, content_type='', precondition=''):
        self.__name__ = id
        self.title = title
        self.precondition = precondition

        data, size = self._read_data(file)
        content_type = self._get_content_type(file, data, id, content_type)
        self.update_data(data, content_type, size)

    def _if_modified_since_request_handler(self, REQUEST, RESPONSE):
        # HTTP If-Modified-Since header handling: return True if
        # we can handle this request by returning a 304 response
        header = REQUEST.get_header('If-Modified-Since', None)
        if header is not None:
            header = header.split(';')[0]
            # Some proxies seem to send invalid date strings for this
            # header. If the date string is not valid, we ignore it
            # rather than raise an error to be generally consistent
            # with common servers such as Apache (which can usually
            # understand the screwy date string as a lucky side effect
            # of the way they parse it).
            # This happens to be what RFC2616 tells us to do in the face of an
            # invalid date.
            try:
                mod_since = int(DateTime(header).timeTime())
            except Exception:
                mod_since = None
            if mod_since is not None:
                if self._p_mtime:
                    last_mod = int(self._p_mtime)
                else:
                    last_mod = 0
                if last_mod > 0 and last_mod <= mod_since:
                    RESPONSE.setHeader(
                        'Last-Modified', rfc1123_date(self._p_mtime)
                    )
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
                    date = if_range.split(';')[0]
                    try:
                        mod_since = int(DateTime(date).timeTime())
                    except Exception:
                        mod_since = None
                    if mod_since is not None:
                        if self._p_mtime:
                            last_mod = int(self._p_mtime)
                        else:
                            last_mod = 0
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
                    RESPONSE.setHeader(
                        'Content-Range', 'bytes */%d' % self.size
                    )
                    RESPONSE.setHeader('Accept-Ranges', 'bytes')
                    RESPONSE.setHeader(
                        'Last-Modified', rfc1123_date(self._p_mtime)
                    )
                    RESPONSE.setHeader('Content-Type', self.content_type)
                    RESPONSE.setHeader('Content-Length', self.size)
                    RESPONSE.setStatus(416)
                    return True

                ranges = HTTPRangeSupport.expandRanges(ranges, self.size)

                if len(ranges) == 1:
                    # Easy case, set extra header and return partial set.
                    start, end = ranges[0]
                    size = end - start

                    RESPONSE.setHeader(
                        'Last-Modified', rfc1123_date(self._p_mtime)
                    )
                    RESPONSE.setHeader('Content-Type', self.content_type)
                    RESPONSE.setHeader('Content-Length', size)
                    RESPONSE.setHeader('Accept-Ranges', 'bytes')
                    RESPONSE.setHeader(
                        'Content-Range',
                        'bytes %d-%d/%d' % (start, end - 1, self.size)
                    )
                    RESPONSE.setStatus(206)  # Partial content

                    data = self.data
                    if isinstance(data, bytes):
                        RESPONSE.write(data[start:end])
                        return True

                    # Linked Pdata objects. Urgh.
                    pos = 0
                    while data is not None:
                        length = len(data.data)
                        pos = pos + length
                        if pos > start:
                            # We are within the range
                            lstart = length - (pos - start)

                            if lstart < 0:
                                lstart = 0

                            # find the endpoint
                            if end <= pos:
                                lend = length - (pos - end)

                                # Send and end transmission
                                RESPONSE.write(data[lstart:lend])
                                break

                            # Not yet at the end, transmit what we have.
                            RESPONSE.write(data[lstart:])

                        data = data.next

                    return True

                else:
                    boundary = _make_boundary()

                    # Calculate the content length
                    size = (8 + len(boundary)  # End marker length
                            + len(ranges) * (  # Constant lenght per set
                                49 + len(boundary)
                                + len(self.content_type)
                                + len('%d' % self.size)))
                    for start, end in ranges:
                        # Variable length per set
                        size = (size + len('%d%d' % (start, end - 1))
                                + end - start)

                    # Some clients implement an earlier draft of the spec, they
                    # will only accept x-byteranges.
                    draftprefix = (request_range is not None) and 'x-' or ''

                    RESPONSE.setHeader('Content-Length', size)
                    RESPONSE.setHeader('Accept-Ranges', 'bytes')
                    RESPONSE.setHeader(
                        'Last-Modified', rfc1123_date(self._p_mtime)
                    )
                    RESPONSE.setHeader(
                        'Content-Type',
                        f'multipart/{draftprefix}byteranges;'
                        f' boundary={boundary}'
                    )
                    RESPONSE.setStatus(206)  # Partial content

                    data = self.data
                    # The Pdata map allows us to jump into the Pdata chain
                    # arbitrarily during out-of-order range searching.
                    pdata_map = {}
                    pdata_map[0] = data

                    for start, end in ranges:
                        RESPONSE.write(
                            b'\r\n--'
                            + boundary.encode('ascii')
                            + b'\r\n'
                        )
                        RESPONSE.write(
                            b'Content-Type: '
                            + self.content_type.encode('ascii')
                            + b'\r\n'
                        )
                        RESPONSE.write(
                            b'Content-Range: bytes '
                            + str(start).encode('ascii')
                            + b'-'
                            + str(end - 1).encode('ascii')
                            + b'/'
                            + str(self.size).encode('ascii')
                            + b'\r\n\r\n'
                        )

                        if isinstance(data, bytes):
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
                                    ((start - first_size) >> 16 << 16)
                                    + first_size
                                )
                            pos = min(closest_pos, max(pdata_map.keys()))
                            data = pdata_map[pos]

                            while data is not None:
                                length = len(data.data)
                                pos = pos + length
                                if pos > start:
                                    # We are within the range
                                    lstart = length - (pos - start)

                                    if lstart < 0:
                                        lstart = 0

                                    # find the endpoint
                                    if end <= pos:
                                        lend = length - (pos - end)

                                        # Send and loop to next range
                                        RESPONSE.write(data[lstart:lend])
                                        break

                                    # Not yet at the end,
                                    # transmit what we have.
                                    RESPONSE.write(data[lstart:])

                                data = data.next
                                # Store a reference to a Pdata chain link
                                # so we don't have to deref during
                                # this request again.
                                pdata_map[pos] = data

                    # Do not keep the link references around.
                    del pdata_map

                    RESPONSE.write(
                        b'\r\n--' + boundary.encode('ascii') + b'--\r\n')
                    return True

    @security.protected(View)
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
            return b''

        if self.precondition and hasattr(self, str(self.precondition)):
            # Grab whatever precondition was defined and then
            # execute it.  The precondition will raise an exception
            # if something violates its terms.
            c = getattr(self, str(self.precondition))
            if hasattr(c, 'isDocTemp') and c.isDocTemp:
                c(REQUEST['PARENTS'][1], REQUEST)
            else:
                c()

        if self._range_request_handler(REQUEST, RESPONSE):
            # we served a chunk of content in response to a range request.
            return b''

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

        data = self.data
        if isinstance(data, bytes):
            RESPONSE.setBase(None)
            return data

        while data is not None:
            RESPONSE.write(data.data)
            data = data.next

        return b''

    @security.protected(View)
    def view_image_or_file(self, URL1):
        """The default view of the contents of the File or Image."""
        raise Redirect(URL1)

    @security.protected(View)
    def PrincipiaSearchSource(self):
        """Allow file objects to be searched."""
        if self.content_type.startswith('text/'):
            return bytes(self.data)
        return b''

    @security.private
    def update_data(self, data, content_type=None, size=None):
        if isinstance(data, str):
            raise TypeError('Data can only be bytes or file-like. '
                            'Unicode objects are expressly forbidden.')

        if content_type is not None:
            self.content_type = content_type
        if size is None:
            size = len(data)
        self.size = size
        self.data = data
        self.ZCacheable_invalidate()
        self.ZCacheable_set(None)
        self.http__refreshEtag()

    def _get_encoding(self):
        """Get the canonical encoding for ZMI."""
        return ZPublisher.HTTPRequest.default_encoding

    @security.protected(change_images_and_files)
    def manage_edit(
        self,
        title,
        content_type,
        precondition='',
        filedata=None,
        REQUEST=None
    ):
        """
        Changes the title and content type attributes of the File or Image.
        """
        if self.wl_isLocked():
            raise ResourceLockedError("File is locked.")

        self.title = str(title)
        self.content_type = str(content_type)
        if precondition:
            self.precondition = str(precondition)
        elif self.precondition:
            del self.precondition
        if filedata is not None:
            if isinstance(filedata, str):
                filedata = filedata.encode(self._get_encoding())
            self.update_data(filedata, content_type, len(filedata))
        else:
            self.ZCacheable_invalidate()

        notify(ObjectModifiedEvent(self))

        if REQUEST:
            message = "Saved changes."
            return self.manage_main(
                self, REQUEST, manage_tabs_message=message)

    @security.protected(change_images_and_files)
    def manage_upload(self, file='', REQUEST=None):
        """
        Replaces the current contents of the File or Image object with file.

        The file or images contents are replaced with the contents of 'file'.
        """
        if self.wl_isLocked():
            raise ResourceLockedError("File is locked.")

        if file:
            data, size = self._read_data(file)
            content_type = self._get_content_type(file, data, self.__name__,
                                                  'application/octet-stream')
            self.update_data(data, content_type, size)
            notify(ObjectModifiedEvent(self))
            msg = 'Saved changes.'
        else:
            msg = 'Please select a file to upload.'

        if REQUEST:
            return self.manage_main(
                self, REQUEST, manage_tabs_message=msg)

    def _get_content_type(self, file, body, id, content_type=None):
        headers = getattr(file, 'headers', None)
        if headers and 'content-type' in headers:
            content_type = headers['content-type']
        else:
            if not isinstance(body, bytes):
                body = body.data
            content_type, enc = guess_content_type(
                getattr(file, 'filename', id), body, content_type)
        return content_type

    def _read_data(self, file):
        import transaction

        n = 1 << 16

        if isinstance(file, str):
            raise ValueError("Must be bytes")

        if isinstance(file, bytes):
            size = len(file)
            if size < n:
                return (file, size)
            # Big string: cut it into smaller chunks
            file = BytesIO(file)

        if isinstance(file, FileUpload) and not file:
            raise ValueError('File not specified')

        if hasattr(file, '__class__') and file.__class__ is Pdata:
            size = len(file)
            return (file, size)

        seek = file.seek
        read = file.read

        seek(0, 2)
        size = end = file.tell()

        if size <= 2 * n:
            seek(0)
            if size < n:
                return read(size), size
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
        _next = None
        while end > 0:
            pos = end - n
            if pos < n:
                pos = 0  # we always want at least n bytes
            seek(pos)

            # Create the object and assign it a next pointer
            # in the same transaction, so that there is only
            # a single database update for it.
            data = Pdata(read(end - pos))
            self._p_jar.add(data)
            data.next = _next

            # Save the object so that we can release its memory.
            transaction.savepoint(optimistic=True)
            data._p_deactivate()
            # The object should be assigned an oid and be a ghost.
            assert data._p_oid is not None
            assert data._p_state == -1

            _next = data
            end = pos

        return (_next, size)

    @security.protected(change_images_and_files)
    def PUT(self, REQUEST, RESPONSE):
        """Handle HTTP PUT requests"""
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        type = REQUEST.get_header('content-type', None)

        file = REQUEST['BODYFILE']

        data, size = self._read_data(file)
        if isinstance(data, str):
            data = data.encode('UTF-8')
        content_type = self._get_content_type(file, data, self.__name__,
                                              type or self.content_type)
        self.update_data(data, content_type, size)

        RESPONSE.setStatus(204)
        return RESPONSE

    @security.protected(View)
    def get_size(self):
        # Get the size of a file or image.
        # Returns the size of the file or image.
        size = self.size
        if size is None:
            size = len(self.data)
        return size

    # deprecated; use get_size!
    getSize = get_size

    @security.protected(View)
    def getContentType(self):
        # Get the content type of a file or image.
        # Returns the content type (MIME type) of a file or image.
        return self.content_type

    def __bytes__(self):
        return bytes(self.data)

    def __str__(self):
        """In most cases, this is probably not what you want. Use ``bytes``."""
        if isinstance(self.data, Pdata):
            return bytes(self.data).decode(self._get_encoding())
        else:
            return self.data.decode(self._get_encoding())

    def __bool__(self):
        return True

    __nonzero__ = __bool__

    def __len__(self):
        data = bytes(self.data)
        return len(data)

    @security.protected(webdav_access)
    def manage_DAVget(self):
        """Return body for WebDAV."""
        RESPONSE = self.REQUEST.RESPONSE

        if self.ZCacheable_isCachingEnabled():
            result = self.ZCacheable_get(default=None)
            if result is not None:
                # We will always get None from RAMCacheManager but we will
                # get something implementing the IStreamIterator interface
                # from FileCacheManager.
                # the content-length is required here by HTTPResponse.
                RESPONSE.setHeader('Content-Length', self.size)
                return result

        data = self.data
        if isinstance(data, bytes):
            RESPONSE.setBase(None)
            return data

        while data is not None:
            RESPONSE.write(data.data)
            data = data.next

        return b''


InitializeClass(File)


manage_addImageForm = DTMLFile(
    'dtml/imageAdd',
    globals(),
    Kind='Image',
    kind='image',
)


def manage_addImage(
    self,
    id,
    file,
    title='',
    precondition='',
    content_type='',
    REQUEST=None
):
    """
    Add a new Image object.

    Creates a new Image object 'id' with the contents of 'file'.
    """
    id = str(id)
    title = str(title)
    content_type = str(content_type)
    precondition = str(precondition)

    id, title = cookId(id, title, file)

    self = self.this()

    # First, we create the image without data:
    self._setObject(id, Image(id, title, b'', content_type, precondition))

    newFile = self._getOb(id)

    # Now we "upload" the data.  By doing this in two steps, we
    # can use a database trick to make the upload more efficient.
    if file:
        newFile.manage_upload(file)
    if content_type:
        newFile.content_type = content_type

    notify(ObjectCreatedEvent(newFile))

    if REQUEST is not None:
        try:
            url = self.DestinationURL()
        except Exception:
            url = REQUEST['URL1']
        REQUEST.RESPONSE.redirect('%s/manage_main' % url)
    return id


def getImageInfo(data):
    data = bytes(data)
    size = len(data)
    height = -1
    width = -1
    content_type = ''

    # handle GIFs
    if (size >= 10) and data[:6] in (b'GIF87a', b'GIF89a'):
        # Check to see if content_type is correct
        content_type = 'image/gif'
        w, h = struct.unpack("<HH", data[6:10])
        width = int(w)
        height = int(h)

    # See PNG v1.2 spec (http://www.cdrom.com/pub/png/spec/)
    # Bytes 0-7 are below, 4-byte chunk length, then 'IHDR'
    # and finally the 4-byte width, height
    elif (size >= 24
          and data[:8] == b'\211PNG\r\n\032\n'
          and data[12:16] == b'IHDR'):
        content_type = 'image/png'
        w, h = struct.unpack(">LL", data[16:24])
        width = int(w)
        height = int(h)

    # Maybe this is for an older PNG version.
    elif (size >= 16) and (data[:8] == b'\211PNG\r\n\032\n'):
        # Check to see if we have the right content type
        content_type = 'image/png'
        w, h = struct.unpack(">LL", data[8:16])
        width = int(w)
        height = int(h)

    # handle JPEGs
    elif (size >= 2) and (data[:2] == b'\377\330'):
        content_type = 'image/jpeg'
        jpeg = BytesIO(data)
        jpeg.read(2)
        b = jpeg.read(1)
        try:
            while (b and ord(b) != 0xDA):
                while (ord(b) != 0xFF):
                    b = jpeg.read(1)
                while (ord(b) == 0xFF):
                    b = jpeg.read(1)
                if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                    jpeg.read(3)
                    h, w = struct.unpack(">HH", jpeg.read(4))
                    break
                else:
                    jpeg.read(int(struct.unpack(">H", jpeg.read(2))[0]) - 2)
                b = jpeg.read(1)
            width = int(w)
            height = int(h)
        except Exception:
            pass

    return content_type, width, height


class Image(File):
    """Image objects can be GIF, PNG or JPEG and have the same methods
    as File objects.  Images also have a string representation that
    renders an HTML 'IMG' tag.
    """

    meta_type = 'Image'
    zmi_icon = 'far fa-file-image'

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    alt = ''
    height = ''
    width = ''

    # FIXME: Redundant, already in base class
    security.declareProtected(change_images_and_files, 'manage_edit')  # NOQA: D001,E501
    security.declareProtected(change_images_and_files, 'manage_upload')  # NOQA: D001,E501
    security.declareProtected(View, 'index_html')  # NOQA: D001
    security.declareProtected(View, 'get_size')  # NOQA: D001
    security.declareProtected(View, 'getContentType')  # NOQA: D001

    _properties = (
        {'id': 'title', 'type': 'string'},
        {'id': 'alt', 'type': 'string'},
        {'id': 'content_type', 'type': 'string', 'mode': 'w'},
        {'id': 'height', 'type': 'string'},
        {'id': 'width', 'type': 'string'},
    )

    manage_options = (
        ({'label': 'Edit', 'action': 'manage_main'},
         {'label': 'View', 'action': 'view_image_or_file'})
        + PropertyManager.manage_options
        + RoleManager.manage_options
        + Item_w__name__.manage_options
        + Cacheable.manage_options
    )

    manage_editForm = DTMLFile(
        'dtml/imageEdit',
        globals(),
        Kind='Image',
        kind='image',
    )
    manage_editForm._setName('manage_editForm')

    security.declareProtected(View, 'view_image_or_file')  # NOQA: D001
    view_image_or_file = DTMLFile('dtml/imageView', globals())

    security.declareProtected(view_management_screens, 'manage')  # NOQA: D001
    security.declareProtected(view_management_screens, 'manage_main')  # NOQA: D001,E501
    manage = manage_main = manage_editForm
    manage_uploadForm = manage_editForm

    @security.private
    def update_data(self, data, content_type=None, size=None):
        if isinstance(data, str):
            raise TypeError('Data can only be bytes or file-like.  '
                            'Unicode objects are expressly forbidden.')

        if size is None:
            size = len(data)

        self.size = size
        self.data = data

        ct, width, height = getImageInfo(data)
        if ct:
            content_type = ct
        if width >= 0 and height >= 0:
            self.width = width
            self.height = height

        # Now we should have the correct content type, or still None
        if content_type is not None:
            self.content_type = content_type

        self.ZCacheable_invalidate()
        self.ZCacheable_set(None)
        self.http__refreshEtag()

    def __bytes__(self):
        return self.tag().encode('utf-8')

    def __str__(self):
        return self.tag()

    @security.protected(View)
    def tag(
        self,
        height=None,
        width=None,
        alt=None,
        scale=0,
        xscale=0,
        yscale=0,
        css_class=None,
        title=None,
        **args
    ):
        """Generate an HTML IMG tag for this image, with customization.

        Arguments to self.tag() can be any valid attributes of an IMG tag.
        'src' will always be an absolute pathname, to prevent redundant
        downloading of images. Defaults are applied intelligently for
        'height', 'width', and 'alt'. If specified, the 'scale', 'xscale',
        and 'yscale' keyword arguments will be used to automatically adjust
        the output height and width values of the image tag.
        #
        Since 'class' is a Python reserved word, it cannot be passed in
        directly in keyword arguments which is a problem if you are
        trying to use 'tag()' to include a CSS class. The tag() method
        will accept a 'css_class' argument that will be converted to
        'class' in the output tag to work around this.
        """
        if height is None:
            height = self.height
        if width is None:
            width = self.width

        # Auto-scaling support
        xdelta = xscale or scale
        ydelta = yscale or scale

        if xdelta and width:
            width = str(int(round(int(width) * xdelta)))
        if ydelta and height:
            height = str(int(round(int(height) * ydelta)))

        result = '<img src="%s"' % (self.absolute_url())

        if alt is None:
            alt = getattr(self, 'alt', '')
        result = f'{result} alt="{html.escape(alt, True)}"'

        if title is None:
            title = getattr(self, 'title', '')
        result = f'{result} title="{html.escape(title, True)}"'

        if height:
            result = f'{result} height="{height}"'

        if width:
            result = f'{result} width="{width}"'

        if css_class is not None:
            result = f'{result} class="{css_class}"'

        for key in list(args.keys()):
            value = args.get(key)
            if value:
                result = f'{result} {key}="{value}"'

        return '%s />' % result


InitializeClass(Image)


def cookId(id, title, file):
    if not id and hasattr(file, 'filename'):
        filename = file.filename
        title = title or filename
        id = filename[max(filename.rfind('/'),
                          filename.rfind('\\'),
                          filename.rfind(':'),
                          ) + 1:]
    return id, title


class Pdata(Persistent, Implicit):
    # Wrapper for possibly large data

    next = None

    def __init__(self, data):
        self.data = data

    def __getitem__(self, key):
        return self.data[key]

    def __len__(self):
        data = bytes(self)
        return len(data)

    def __bytes__(self):
        _next = self.next
        if _next is None:
            return self.data

        r = [self.data]
        while _next is not None:
            self = _next
            r.append(self.data)
            _next = self.next

        return b''.join(r)
