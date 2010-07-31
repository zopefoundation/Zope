##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""Mount point (stored in ZODB).
"""

import os
import sys
import traceback
from cStringIO import StringIO
from logging import getLogger

import transaction

from AccessControl.class_init import InitializeClass
from Acquisition import ImplicitAcquisitionWrapper
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from OFS.SimpleItem import SimpleItem
from OFS.Folder import Folder
from OFS.Folder import manage_addFolder
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

LOG = getLogger('Zope.ZODBMountPoint')

_www = os.path.join(os.path.dirname(__file__), 'www')

def getConfiguration():
    from App.config import getConfiguration
    return getConfiguration().dbtab

class SimpleTrailblazer:
    """Follows Zope paths.  If a path is not found, creates a Folder.

    Respects Zope security.
    """

    restricted = 1

    def __init__(self, base):
        self.base = base

    def _construct(self, context, id):
        """Creates and returns the named folder."""
        manage_addFolder(context, id)
        o = context.restrictedTraverse(id)
        context._p_jar.add(aq_base(o))
        return o

    def traverseOrConstruct(self, path, omit_final=0):
        """Traverses a path, constructing it if necessary."""
        container = self.base
        parts = filter(None, path.split('/'))
        if omit_final:
            if len(parts) < 1:
                raise ValueError, 'Path %s is not a valid mount path' % path
            parts = parts[:-1]
        for part in parts:
            try:
                if self.restricted:
                    container = container.restrictedTraverse(part)
                else:
                    container = container.unrestrictedTraverse(part)
            except (KeyError, AttributeError):
                # Try to create a container in this place.
                container = self._construct(container, part)
        return container

class CustomTrailblazer (SimpleTrailblazer):
    """Like SimpleTrailblazer but creates custom objects.

    Does not respect Zope security because this may be invoked before
    security and products get initialized.
    """

    restricted = 0

    def __init__(self, base, container_class=None):
        self.base = base
        if not container_class:
            container_class = 'OFS.Folder.Folder'
        pos = container_class.rfind('.')
        if pos < 0:
            raise ValueError("Not a valid container_class: %s" % repr(
                container_class))
        self.module_name = container_class[:pos]
        self.class_name = container_class[pos + 1:]

    def _construct(self, context, id):
        """Creates and returns the named object."""
        jar = self.base._p_jar
        klass = jar.db().classFactory(jar, self.module_name, self.class_name)
        obj = klass(id)
        obj._setId(id)
        context._setObject(id, obj)
        obj = context.unrestrictedTraverse(id)
        # Commit a subtransaction to assign the new object to
        # the correct database.
        transaction.savepoint(optimistic=True)
        return obj


class MountedObject(SimpleItem):
    '''A database mount point with a basic interface for displaying the
    reason the database did not connect.
    '''
    meta_type = 'ZODB Mount Point'
    _isMountedObject = 1
    # DM 2005-05-17: default value change necessary after fix of
    # '_create_mount_point' handling
    #_create_mount_points = 0
    _create_mount_points = True

    icon = 'p_/broken'
    manage_options = ({'label':'Traceback', 'action':'manage_traceback'},)
    _v_mount_params = None
    _v_data = None
    _v_connect_error = None

    manage_traceback = PageTemplateFile('mountfail.pt', _www)

    def __init__(self, path):
        path = str(path)
        self._path = path
        id = path.split('/')[-1]
        self.id = id

    def _getMountedConnection(self, anyjar):
        # This creates the DB if it doesn't exist yet and adds it
        # to the multidatabase
        self._getDB()
        # Return a new or existing connection linked to the multidatabase set
        return anyjar.get_connection(self._getDBName())

    def mount_error_(self):
        return self._v_connect_error

    def _getDB(self):
        """Hook for getting the DB object for this mount point.
        """
        return getConfiguration().getDatabase(self._path)

    def _getDBName(self):
        """Hook for getting the name of the database for this mount point.
        """
        return getConfiguration().getDatabaseFactory(self._path).getName()

    def _getRootDBName(self):
        """Hook for getting the name of the root database.
        """
        return getConfiguration().getDatabaseFactory('/').getName()

    def _loadMountParams(self):
        factory = getConfiguration().getDatabaseFactory(self._path)
        params = factory.getMountParams(self._path)
        self._v_mount_params = params
        return params

    def _traverseToMountedRoot(self, root, mount_parent):
        """Hook for getting the object to be mounted.
        """
        params = self._v_mount_params
        if params is None:
            params = self._loadMountParams()
        real_root, real_path, container_class = params
        if real_root is None:
            real_root = 'Application'
        try:
            obj = root[real_root]
        except KeyError:
            # DM 2005-05-17: why should we require 'container_class'?
            #if container_class or self._create_mount_points:
            if self._create_mount_points:
                # Create a database automatically.
                from OFS.Application import Application
                obj = Application()
                root[real_root] = obj
                # Get it into the database
                transaction.savepoint(optimistic=True)
            else:
                raise

        if real_path is None:
            real_path = self._path
        if real_path and real_path != '/':
            try:
                obj = obj.unrestrictedTraverse(real_path)
            except (KeyError, AttributeError):
                # DM 2005-05-13: obviously, we do not want automatic
                #  construction when "_create_mount_points" is false
                #if container_class or self._create_mount_points:
                if container_class and self._create_mount_points:
                    blazer = CustomTrailblazer(obj, container_class)
                    obj = blazer.traverseOrConstruct(real_path)
                else:
                    raise
        return obj

    def _logConnectException(self):
        '''Records info about the exception that just occurred.
        '''
        exc = sys.exc_info()
        LOG.error('Failed to mount database. %s (%s)' % exc[:2], exc_info=exc)
        f=StringIO()
        traceback.print_tb(exc[2], 100, f)
        self._v_connect_error = (exc[0], exc[1], f.getvalue())
        exc = None


    def __of__(self, parent):
        # Accesses the database, returning an acquisition
        # wrapper around the connected object rather than around self.
        try:
            return self._getOrOpenObject(parent)
        except:
            return ImplicitAcquisitionWrapper(self, parent)


    def _test(self, parent):
        '''Tests the database connection.
        '''
        self._getOrOpenObject(parent)
        return 1

    def _getOrOpenObject(self, parent):
        t = self._v_data
        if t is not None:
            data = t[0]
        else:
            self._v_connect_error = None
            conn = None
            try:
                anyjar = self._p_jar
                if anyjar is None:
                    anyjar = parent._p_jar
                conn = self._getMountedConnection(anyjar)
                root = conn.root()
                obj = self._traverseToMountedRoot(root, parent)
                data = aq_base(obj)
                # Store the data object in a tuple to hide from acquisition.
                self._v_data = (data,)
            except:
                # Possibly broken database.
                self._logConnectException()
                raise

            try:
                # XXX This method of finding the mount point is deprecated.
                # Do not use the _v_mount_point_ attribute.
                data._v_mount_point_ = (aq_base(self),)
            except:
                # Might be a read-only object.
                pass

        return data.__of__(parent)

    def __repr__(self):
        return "%s(id=%s)" % (self.__class__.__name__, repr(self.id))


InitializeClass(MountedObject)


def getMountPoint(ob):
    """Gets the mount point for a mounted object.

    Returns None if the object is not a mounted object.
    """
    container = aq_parent(aq_inner(ob))
    mps = getattr(container, '_mount_points', None)
    if mps:
        mp = mps.get(ob.getId())
        if mp is not None and (mp._p_jar is ob._p_jar or ob._p_jar is None):
            # Since the mount point and the mounted object are from
            # the same connection, the mount point must have been
            # replaced.  The object is not mounted after all.
            return None
        # else the object is mounted.
        return mp
    return None


def setMountPoint(container, id, mp):
    mps = getattr(container, '_mount_points', None)
    if mps is None:
        container._mount_points = {id: aq_base(mp)}
    else:
        container._p_changed = 1
        mps[id] = aq_base(mp)


manage_addMountsForm = PageTemplateFile('addMountsForm.pt', _www)

def manage_getMountStatus(dispatcher):
    """Returns the status of each mount point specified by zope.conf
    """
    res = []
    conf = getConfiguration()
    items = conf.listMountPaths()
    items.sort()
    root = dispatcher.getPhysicalRoot()
    for path, name in items:
        if not path or path == '/':
            # Ignore the root mount.
            continue
        o = root.unrestrictedTraverse(path, None)
        # Examine the _v_mount_point_ attribute to verify traversal
        # to the correct mount point.
        if o is None:
            exists = 0
            status = 'Ready to create'
        elif getattr(o, '_isMountedObject', 0):
            # Oops, didn't actually mount!
            exists = 1
            t, v = o._v_connect_error[:2]
            status = '%s: %s' % (t, v)
        else:
            exists = 1
            mp = getMountPoint(o)
            if mp is None:
                mp_old = getattr(o, '_v_mount_point_', None)
                if mp_old is not None:
                    # Use the old method of accessing mount points
                    # to update to the new method.
                    # Update the container right now.
                    setMountPoint(dispatcher.this(), o.getId(), mp_old[0])
                    status = 'Ok (updated)'
                else:
                    status = '** Something is in the way **'
            else:
                mp_path = getattr(mp, '_path', None)
                if mp_path != path:
                    status = '** Set to wrong path: %s **' % repr(mp_path)
                else:
                    status = 'Ok'
        res.append({
            'path': path, 'name': name, 'exists': exists,
            'status': status,
            })
    return res


# DM 2005-05-17: change default for 'create_mount_points' as
#  otherwise (after our fix) 'temp_folder' can no longer be mounted
#def manage_addMounts(dispatcher, paths=(), create_mount_points=0,
def manage_addMounts(dispatcher, paths=(), create_mount_points=True,
                     REQUEST=None):
    """Adds MountedObjects at the requested paths.
    """
    count = 0
    app = dispatcher.getPhysicalRoot()
    for path in paths:
        mo = MountedObject(path)
        mo._create_mount_points = not not create_mount_points
        # Raise an error now if there is any problem.
        mo._test(app)
        blazer = SimpleTrailblazer(app)
        container = blazer.traverseOrConstruct(path, omit_final=1)
        container._p_jar.add(mo)
        loaded = mo.__of__(container)

        # Add a faux object to avoid generating manage_afterAdd() events
        # while appeasing OFS.ObjectManager._setObject(), then discreetly
        # replace the faux object with a MountedObject.
        faux = Folder()
        faux.id = mo.id
        faux.meta_type = loaded.meta_type
        container._setObject(faux.id, faux)
        # DM 2005-05-17: we want to keep our decision about automatic
        #  mount point creation
        #del mo._create_mount_points
        container._setOb(faux.id, mo)
        setMountPoint(container, faux.id, mo)
        count += 1
    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(
            REQUEST['URL1'] + ('/manage_main?manage_tabs_message='
            'Added %d mount points.' % count))
