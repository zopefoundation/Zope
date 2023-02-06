##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""WebDAV xml request objects.
"""

import sys
from io import StringIO
from urllib.parse import quote

import transaction
from AccessControl.Permissions import delete_objects
from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_parent
from OFS.interfaces import IWriteLock
from OFS.LockItem import LockItem
from webdav.common import Locked
from webdav.common import PreconditionFailed
from webdav.common import absattr
from webdav.common import isDavCollection
from webdav.common import urlbase
from webdav.common import urlfix
from webdav.common import urljoin
from webdav.PropertySheets import DAVProperties
from webdav.xmltools import XmlParser
from zExceptions import BadRequest
from zExceptions import Forbidden
from zExceptions import HTTPPreconditionFailed
from zExceptions import MethodNotAllowed
from zExceptions import ResourceLockedError


def safe_quote(url, mark=r'%'):
    if url.find(mark) > -1:
        return url
    return quote(url)


class DAVProps(DAVProperties):
    """Emulate required DAV properties for objects which do
       not themselves support properties. This is mainly so
       that non-PropertyManagers can appear to support DAV
       PROPFIND requests."""

    def __init__(self, obj):
        self.__obj__ = obj

    def v_self(self):
        return self.__obj__

    p_self = v_self


class PropFind:
    """Model a PROPFIND request."""

    def __init__(self, request):
        self.request = request
        self.depth = 'infinity'
        self.allprop = 0
        self.propname = 0
        self.propnames = []
        self.parse(request)

    def parse(self, request, dav='DAV:'):
        self.depth = request.get_header('Depth', 'infinity')
        if not (self.depth in ('0', '1', 'infinity')):
            raise BadRequest('Invalid Depth header.')
        body = request.get('BODY', '')
        self.allprop = (not len(body))
        if not body:
            return
        try:
            root = XmlParser().parse(body)
        except Exception:
            raise BadRequest(sys.exc_info()[1])
        e = root.elements('propfind', ns=dav)
        if not e:
            raise BadRequest('Invalid xml request.')
        e = e[0]
        if e.elements('allprop', ns=dav):
            self.allprop = 1
            return
        if e.elements('propname', ns=dav):
            self.propname = 1
            return
        prop = e.elements('prop', ns=dav)
        if not prop:
            raise BadRequest('Invalid xml request.')
        prop = prop[0]
        for val in prop.elements():
            self.propnames.append((val.name(), val.namespace()))
        if (not self.allprop) and (not self.propname) and \
           (not self.propnames):
            raise BadRequest('Invalid xml request.')
        return

    def apply(self, obj, url=None, depth=0, result=None, top=1):
        if result is None:
            result = StringIO()
            depth = self.depth
            url = urlfix(self.request['URL'], 'PROPFIND')
            url = urlbase(url)
            result.write('<?xml version="1.0" encoding="utf-8"?>\n'
                         '<d:multistatus xmlns:d="DAV:">\n')
        iscol = isDavCollection(obj)
        if iscol and url[-1] != '/':
            url = url + '/'
        result.write('<d:response>\n<d:href>%s</d:href>\n' % safe_quote(url))
        if hasattr(aq_base(obj), 'propertysheets'):
            propsets = obj.propertysheets.values()
            obsheets = obj.propertysheets
        else:
            davprops = DAVProps(obj)
            propsets = (davprops,)
            obsheets = {'DAV:': davprops}
        if self.allprop:
            stats = []
            for ps in propsets:
                if hasattr(aq_base(ps), 'dav__allprop'):
                    stats.append(ps.dav__allprop())
            stats = ''.join(stats) or '<d:status>200 OK</d:status>\n'
            result.write(stats)
        elif self.propname:
            stats = []
            for ps in propsets:
                if hasattr(aq_base(ps), 'dav__propnames'):
                    stats.append(ps.dav__propnames())
            stats = ''.join(stats) or '<d:status>200 OK</d:status>\n'
            result.write(stats)
        elif self.propnames:
            rdict = {}
            for name, ns in self.propnames:
                ps = obsheets.get(ns, None)
                if ps is not None and hasattr(aq_base(ps), 'dav__propstat'):
                    ps.dav__propstat(name, rdict)
                else:
                    prop = f'<n:{name} xmlns:n="{ns}"/>'
                    code = '404 Not Found'
                    if code not in rdict:
                        rdict[code] = [prop]
                    else:
                        rdict[code].append(prop)
            keys = list(rdict.keys())
            for key in sorted(keys):
                result.write('<d:propstat>\n'
                             '  <d:prop>\n'
                             )
                [result.write(x) for x in rdict[key]]
                result.write('  </d:prop>\n'
                             '  <d:status>HTTP/1.1 %s</d:status>\n'
                             '</d:propstat>\n' % key
                             )
        else:
            raise BadRequest('Invalid request')
        result.write('</d:response>\n')
        if depth in ('1', 'infinity') and iscol:
            for ob in obj.listDAVObjects():
                if hasattr(ob, "meta_type"):
                    if ob.meta_type == "Broken Because Product is Gone":
                        continue
                dflag = hasattr(ob, '_p_changed') and (ob._p_changed is None)
                if hasattr(ob, '__locknull_resource__'):
                    # Do nothing, a null resource shouldn't show up to DAV
                    if dflag:
                        ob._p_deactivate()
                elif hasattr(ob, '__dav_resource__'):
                    uri = urljoin(url, absattr(ob.getId()))
                    depth = depth == 'infinity' and depth or 0
                    self.apply(ob, uri, depth, result, top=0)
                    if dflag:
                        ob._p_deactivate()
        if not top:
            return result
        result.write('</d:multistatus>')

        return result.getvalue()


class PropPatch:
    """Model a PROPPATCH request."""

    def __init__(self, request):
        self.request = request
        self.values = []
        self.parse(request)

    def parse(self, request, dav='DAV:'):
        body = request.get('BODY', '')
        try:
            root = XmlParser().parse(body)
        except Exception:
            raise BadRequest(sys.exc_info()[1])
        vals = self.values
        e = root.elements('propertyupdate', ns=dav)
        if not e:
            raise BadRequest('Invalid xml request.')
        e = e[0]
        for ob in e.elements():
            if ob.name() == 'set' and ob.namespace() == dav:
                proptag = ob.elements('prop', ns=dav)
                if not proptag:
                    raise BadRequest('Invalid xml request.')
                proptag = proptag[0]
                for prop in proptag.elements():
                    # We have to ensure that all tag attrs (including
                    # an xmlns attr for all xml namespaces used by the
                    # element and its children) are saved, per rfc2518.
                    name, ns = prop.name(), prop.namespace()
                    e, attrs = prop.elements(), prop.attrs()
                    if (not e) and (not attrs):
                        # simple property
                        item = (name, ns, prop.strval(), {})
                        vals.append(item)
                    else:
                        # xml property
                        attrs = {}
                        prop.remove_namespace_attrs()
                        for attr in prop.attrs():
                            attrs[attr.qname()] = attr.value()
                        md = {'__xml_attrs__': attrs}
                        item = (name, ns, prop.strval(), md)
                        vals.append(item)
            if ob.name() == 'remove' and ob.namespace() == dav:
                proptag = ob.elements('prop', ns=dav)
                if not proptag:
                    raise BadRequest('Invalid xml request.')
                proptag = proptag[0]
                for prop in proptag.elements():
                    item = (prop.name(), prop.namespace())
                    vals.append(item)

    def apply(self, obj):
        url = urlfix(self.request['URL'], 'PROPPATCH')
        if isDavCollection(obj):
            url = url + '/'
        result = StringIO()
        errors = []
        result.write('<?xml version="1.0" encoding="utf-8"?>\n'
                     '<d:multistatus xmlns:d="DAV:">\n'
                     '<d:response>\n'
                     '<d:href>%s</d:href>\n' % quote(url))
        propsets = obj.propertysheets
        for value in self.values:
            status = '200 OK'
            if len(value) > 2:
                name, ns, val, md = value
                propset = propsets.get(ns, None)
                if propset is None:
                    propsets.manage_addPropertySheet('', ns)
                    propset = propsets.get(ns)
                if propset.hasProperty(name):
                    try:
                        propset._updateProperty(name, val, meta=md)
                    except Exception:
                        errors.append(str(sys.exc_info()[1]))
                        status = '409 Conflict'
                else:
                    try:
                        propset._setProperty(name, val, meta=md)
                    except Exception:
                        errors.append(str(sys.exc_info()[1]))
                        status = '409 Conflict'
            else:
                name, ns = value
                propset = propsets.get(ns, None)
                if propset is None or not propset.hasProperty(name):
                    # removing a non-existing property is not an error!
                    # according to RFC 2518
                    status = '200 OK'
                else:
                    try:
                        propset._delProperty(name)
                    except Exception:
                        errors.append('%s cannot be deleted.' % name)
                        status = '409 Conflict'
            result.write('<d:propstat xmlns:n="%s">\n'
                         '  <d:prop>\n'
                         '  <n:%s/>\n'
                         '  </d:prop>\n'
                         '  <d:status>HTTP/1.1 %s</d:status>\n'
                         '</d:propstat>\n' % (ns, name, status))
        errmsg = '\n'.join(errors) or 'The operation succeeded.'
        result.write('<d:responsedescription>\n'
                     '%s\n'
                     '</d:responsedescription>\n'
                     '</d:response>\n'
                     '</d:multistatus>' % errmsg)
        result = result.getvalue()
        if not errors:
            return result
        # This is lame, but I cant find a way to keep ZPublisher
        # from sticking a traceback into my xml response :(
        transaction.abort()
        result = result.replace('200 OK', '424 Failed Dependency')
        return result


class Lock:
    """Model a LOCK request."""

    def __init__(self, request):
        self.request = request
        data = request.get('BODY', '')
        self.scope = 'exclusive'
        self.type = 'write'
        self.owner = ''
        timeout = request.get_header('Timeout', 'infinite')
        self.timeout = timeout.split(',')[-1].strip()
        self.parse(data)

    def parse(self, data, dav='DAV:'):
        root = XmlParser().parse(data)
        info = root.elements('lockinfo', ns=dav)[0]
        ls = info.elements('lockscope', ns=dav)[0]
        self.scope = ls.elements()[0].name()
        lt = info.elements('locktype', ns=dav)[0]
        self.type = lt.elements()[0].name()

        lockowner = info.elements('owner', ns=dav)
        if lockowner:
            # Since the Owner element may contain children in different
            # namespaces (or none at all), we have to find them for potential
            # remapping.  Note that Cadaver doesn't use namespaces in the
            # XML it sends.
            lockowner = lockowner[0]
            for el in lockowner.elements():
                # name = el.name()
                elns = el.namespace()
                if not elns:
                    # There's no namespace, so we have to add one
                    lockowner.remap({dav: 'ot'})
                    el.__nskey__ = 'ot'
                    for subel in el.elements():
                        if not subel.namespace():
                            el.__nskey__ = 'ot'
                else:
                    el.remap({dav: 'o'})
            self.owner = lockowner.strval()

    def apply(self, obj, creator=None, depth='infinity', token=None,
              result=None, url=None, top=1):
        """ Apply, built for recursion (so that we may lock subitems
        of a collection if requested """

        if result is None:
            result = StringIO()
            url = urlfix(self.request['URL'], 'LOCK')
            url = urlbase(url)
        iscol = isDavCollection(obj)
        if iscol and url[-1] != '/':
            url = url + '/'
        errmsg = None
        exc_ob = None
        lock = None

        try:
            lock = LockItem(creator, self.owner, depth, self.timeout,
                            self.type, self.scope, token)
            if token is None:
                token = lock.getLockToken()

        except ValueError:
            errmsg = "412 Precondition Failed"
            exc_ob = HTTPPreconditionFailed()
        except Exception:
            errmsg = "403 Forbidden"
            exc_ob = Forbidden()

        try:
            if not IWriteLock.providedBy(obj):
                if top:
                    # This is the top level object in the apply, so we
                    # do want an error
                    errmsg = "405 Method Not Allowed"
                    exc_ob = MethodNotAllowed()
                else:
                    # We're in an infinity request and a subobject does
                    # not support locking, so we'll just pass
                    pass
            elif obj.wl_isLocked():
                errmsg = "423 Locked"
                exc_ob = ResourceLockedError()
            else:
                method = getattr(obj, 'wl_setLock')
                vld = getSecurityManager().validate(None, obj, 'wl_setLock',
                                                    method)
                if vld and token and (lock is not None):
                    obj.wl_setLock(token, lock)
                else:
                    errmsg = "403 Forbidden"
                    exc_ob = Forbidden()
        except Exception:
            errmsg = "403 Forbidden"
            exc_ob = Forbidden()

        if errmsg:
            if top and ((depth in (0, '0')) or (not iscol)):
                # We don't need to raise multistatus errors
                raise exc_ob
            elif not result.getvalue():
                # We haven't had any errors yet, so our result is empty
                # and we need to set up the XML header
                result.write('<?xml version="1.0" encoding="utf-8" ?>\n'
                             '<d:multistatus xmlns:d="DAV:">\n')
            result.write('<d:response>\n <d:href>%s</d:href>\n' % url)
            result.write(' <d:status>HTTP/1.1 %s</d:status>\n' % errmsg)
            result.write('</d:response>\n')

        if depth == 'infinity' and iscol:
            for ob in obj.objectValues():
                if hasattr(obj, '__dav_resource__'):
                    uri = urljoin(url, absattr(ob.getId()))
                    self.apply(ob, creator, depth, token, result,
                               uri, top=0)
        if not top:
            return token, result
        if result.getvalue():
            # One or more subitems probably failed, so close the multistatus
            # element and clear out all succesful locks
            result.write('</d:multistatus>')
            transaction.abort()  # This *SHOULD* clear all succesful locks
        return token, result.getvalue()


class Unlock:
    """ Model an Unlock request """

    def apply(self, obj, token, url=None, result=None, top=1):
        if result is None:
            result = StringIO()
            url = urlfix(url, 'UNLOCK')
            url = urlbase(url)
        iscol = isDavCollection(obj)
        if iscol and url[-1] != '/':
            url = url + '/'
        errmsg = None

        islockable = IWriteLock.providedBy(obj)

        if islockable:
            if obj.wl_hasLock(token):
                method = getattr(obj, 'wl_delLock')
                vld = getSecurityManager().validate(
                    None, obj, 'wl_delLock', method)
                if vld:
                    obj.wl_delLock(token)
                else:
                    errmsg = "403 Forbidden"
            else:
                errmsg = '400 Bad Request'
        else:
            # Only set an error message if the command is being applied
            # to a top level object.  Otherwise, we're descending a tree
            # which may contain many objects that don't implement locking,
            # so we just want to avoid them
            if top:
                errmsg = "405 Method Not Allowed"

        if errmsg:
            if top and (not iscol):
                # We don't need to raise multistatus errors
                if errmsg[:3] == '403':
                    raise Forbidden
                else:
                    raise PreconditionFailed
            elif not result.getvalue():
                # We haven't had any errors yet, so our result is empty
                # and we need to set up the XML header
                result.write('<?xml version="1.0" encoding="utf-8" ?>\n'
                             '<d:multistatus xmlns:d="DAV:">\n')
            result.write('<d:response>\n <d:href>%s</d:href>\n' % url)
            result.write(' <d:status>HTTP/1.1 %s</d:status>\n' % errmsg)
            result.write('</d:response>\n')

        if iscol:
            for ob in obj.objectValues():
                if hasattr(ob, '__dav_resource__') and \
                        IWriteLock.providedBy(ob):
                    uri = urljoin(url, absattr(ob.getId()))
                    self.apply(ob, token, uri, result, top=0)
        if not top:
            return result
        if result.getvalue():
            # One or more subitems probably failed, so close the multistatus
            # element and clear out all succesful unlocks
            result.write('</d:multistatus>')
            transaction.abort()
        return result.getvalue()


class DeleteCollection:
    """ With WriteLocks in the picture, deleting a collection involves
    checking *all* descendents (deletes on collections are always of depth
    infinite) for locks and if the locks match. """

    def apply(self, obj, token, sm, url=None, result=None, top=1):
        if result is None:
            result = StringIO()
            url = urlfix(url, 'DELETE')
            url = urlbase(url)
        iscol = isDavCollection(obj)
        errmsg = None
        parent = aq_parent(obj)

        islockable = IWriteLock.providedBy(obj)
        if parent and (not sm.checkPermission(delete_objects, parent)):
            # User doesn't have permission to delete this object
            errmsg = "403 Forbidden"
        elif islockable and obj.wl_isLocked():
            if token and obj.wl_hasLock(token):
                # Object is locked, and the token matches (no error)
                errmsg = ""
            else:
                errmsg = "423 Locked"

        if errmsg:
            if top and (not iscol):
                if errmsg == "403 Forbidden":
                    raise Forbidden()
                if errmsg == "423 Locked":
                    raise Locked()
            elif not result.getvalue():
                # We haven't had any errors yet, so our result is empty
                # and we need to set up the XML header
                result.write('<?xml version="1.0" encoding="utf-8" ?>\n'
                             '<d:multistatus xmlns:d="DAV:">\n')
            result.write('<d:response>\n <d:href>%s</d:href>\n' % url)
            result.write(' <d:status>HTTP/1.1 %s</d:status>\n' % errmsg)
            result.write('</d:response>\n')

        if iscol:
            for ob in obj.objectValues():
                dflag = hasattr(ob, '_p_changed') and (ob._p_changed is None)
                if hasattr(ob, '__dav_resource__'):
                    uri = urljoin(url, absattr(ob.getId()))
                    self.apply(ob, token, sm, uri, result, top=0)
                    if dflag:
                        ob._p_deactivate()
        if not top:
            return result
        if result.getvalue():
            # One or more subitems can't be delted, so close the multistatus
            # element
            result.write('</d:multistatus>\n')
        return result.getvalue()
