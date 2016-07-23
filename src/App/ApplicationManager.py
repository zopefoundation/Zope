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

from logging import getLogger
import os
import sys
from thread import get_ident
import time
import urllib

from AccessControl.class_init import InitializeClass
from AccessControl.requestmethod import requestmethod
from Acquisition import Implicit
from App.CacheManager import CacheManager
from App.config import getConfiguration
from App.special_dtml import DTMLFile
from App.version_txt import version_txt
from OFS.Folder import Folder
from OFS.SimpleItem import Item
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zExceptions import Redirect

LOG = getLogger('ApplicationManager')


class DatabaseManager(Item, Implicit):
    """Database management (legacy)
    """
    manage = manage_main = DTMLFile('dtml/dbMain', globals())
    manage_main._setName('manage_main')
    id = 'DatabaseManagement'
    name = title = 'Database Management'
    meta_type = 'Database Management'

    manage_options = ((
        {'label': 'Database', 'action': 'manage_main'},
        {'label': 'Activity', 'action': 'manage_activity'},
        {'label': 'Cache Parameters', 'action': 'manage_cacheParameters'},
        {'label': 'Flush Cache', 'action': 'manage_cacheGC'},
    ))

    # These need to be here rather to make tabs work correctly. This
    # needs to be revisited.
    manage_activity = DTMLFile('dtml/activity', globals())
    manage_cacheParameters = DTMLFile('dtml/cacheParameters', globals())
    manage_cacheGC = DTMLFile('dtml/cacheGC', globals())

InitializeClass(DatabaseManager)


class FakeConnection:
    # Supports the methods of Connection that CacheManager needs

    def __init__(self, db, parent_jar):
        self._db = db

    def db(self):
        return self._db


class DatabaseChooser(SimpleItem):
    """ Choose which database to view
    """
    meta_type = 'Database Management'
    name = title = 'Database Management'
    isPrincipiaFolderish = 1

    manage_options = (
        {'label': 'Databases', 'action': 'manage_main'},
    )

    manage_main = PageTemplateFile('www/chooseDatabase.pt', globals())

    def __init__(self, id):
        self.id = id

    def getDatabaseNames(self, quote=False):
        configuration = getConfiguration()
        names = configuration.dbtab.listDatabaseNames()
        names.sort()
        if quote:
            return [(name, urllib.quote(name)) for name in names]
        return names

    def __getitem__(self, name):
        configuration = getConfiguration()
        db = configuration.dbtab.getDatabase(name=name)
        m = AltDatabaseManager()
        m.id = name
        m._p_jar = FakeConnection(db, self.getPhysicalRoot()._p_jar)
        return m.__of__(self)

    def __bobo_traverse__(self, request, name):
        configuration = getConfiguration()
        if configuration.dbtab.hasDatabase(name):
            return self[name]
        return getattr(self, name)

    def tpValues(self):
        names = self.getDatabaseNames()
        res = []
        for name in names:
            m = AltDatabaseManager()
            m.id = name
            # Avoid opening the database just for the tree widget.
            m._p_jar = None
            res.append(m.__of__(self))
        return res

InitializeClass(DatabaseChooser)


class ApplicationManager(Folder, CacheManager):
    """System management
    """
    __roles__ = ('Manager',)
    isPrincipiaFolderish = 1
    Database = DatabaseChooser('Database')  # DatabaseManager()

    manage = manage_main = DTMLFile('dtml/cpContents', globals())
    manage_main._setName('manage_main')

    _objects = (
        {'id': 'Database',
         'meta_type': Database.meta_type},
    )

    manage_options = ({'label': 'Control Panel', 'action': 'manage_main'}, )

    id = 'Control_Panel'
    name = title = 'Control Panel'
    meta_type = 'Control Panel'

    process_id = os.getpid()
    process_start = int(time.time())

    # Disable some inappropriate operations
    manage_addObject = None
    manage_delObjects = None
    manage_addProperty = None
    manage_editProperties = None
    manage_delProperties = None

    def _canCopy(self, op=0):
        return 0

    def _init(self):
        pass

    def version_txt(self):
        if not hasattr(self, '_v_version_txt'):
            self._v_version_txt = version_txt()

        return self._v_version_txt

    def sys_version(self):
        return sys.version

    def sys_platform(self):
        return sys.platform

    def manage_app(self, URL2):
        """Return to the main management screen"""
        raise Redirect(URL2 + '/manage')

    def thread_get_ident(self):
        return get_ident()

    def db_name(self):
        return self._p_jar.db().getName()

    def db_size(self):
        s = self._p_jar.db().getSize()
        if isinstance(s, str):
            return s

        if s >= 1048576.0:
            return '%.1fM' % (s / 1048576.0)
        return '%.1fK' % (s / 1024.0)

    @requestmethod('POST')
    def manage_pack(self, days=0, REQUEST=None, _when=None):
        """Pack the database"""

        if _when is None:
            _when = time.time()

        t = _when - (days * 86400)

        db = self._p_jar.db()
        t = db.pack(t)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(
                REQUEST['URL1'] + '/manage_workspace')
        return t

    def getINSTANCE_HOME(self):
        return getConfiguration().instancehome

    def getCLIENT_HOME(self):
        return getConfiguration().clienthome


class AltDatabaseManager(DatabaseManager, CacheManager):
    """ Database management DBTab-style
    """
    db_name = ApplicationManager.db_name.im_func
    db_size = ApplicationManager.db_size.im_func
    manage_pack = ApplicationManager.manage_pack.im_func
