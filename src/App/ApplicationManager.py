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

import os
import sys
import time
from urllib import parse

from AccessControl.class_init import InitializeClass
from AccessControl.requestmethod import requestmethod
from Acquisition import Implicit
from App.config import getConfiguration
from App.DavLockManager import DavLockManager
from App.Management import Tabs
from App.special_dtml import DTMLFile
from App.Undo import UndoSupport
from App.version_txt import version_txt
from OFS.Traversable import Traversable
from Persistence import Persistent
from Products.PageTemplates.PageTemplateFile import PageTemplateFile


class FakeConnection:
    # Supports the methods of Connection that CacheManager needs

    def __init__(self, db, parent_jar):
        self._db = db

    def db(self):
        return self._db


class DatabaseChooser(Tabs, Traversable, Implicit):
    """ Choose which database to view
    """

    __allow_access_to_unprotected_subobjects__ = 1

    id = 'Database'
    name = title = 'Database Management'
    meta_type = 'Database Management'

    manage_main = manage_workspace = PageTemplateFile('www/chooseDatabase.pt',
                                                      globals())
    manage_main.__name__ = 'manage_main'
    manage_main._need__name__ = 0
    manage_options = (
        {'label': 'Control Panel', 'action': '../manage_main'},
        {'label': 'Databases', 'action': 'manage_main'},
        {'label': 'Configuration', 'action': '../Configuration/manage_main'},
    )
    MANAGE_TABS_NO_BANNER = True

    def getDatabaseNames(self, quote=False):
        configuration = getConfiguration()
        names = configuration.dbtab.listDatabaseNames()
        names.sort()
        if quote:
            return [(name, parse.quote(name)) for name in names]
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


InitializeClass(DatabaseChooser)


class ConfigurationViewer(Tabs, Traversable, Implicit):
    """ Provides information about the running configuration
    """
    manage = manage_main = manage_workspace = DTMLFile('dtml/cpConfiguration',
                                                       globals())
    manage_main._setName('manage_main')
    id = 'Configuration'
    name = title = 'Configuration Viewer'
    meta_type = name
    zmi_icon = 'fa fa-cog'
    manage_options = (
        {'label': 'Control Panel', 'action': '../manage_main'},
        {'label': 'Databases', 'action': '../Database/manage_main'},
        {'label': 'Configuration', 'action': 'manage_main'},
        {'label': 'DAV Locks', 'action': '../DavLocks/manage_main'},
    )
    MANAGE_TABS_NO_BANNER = True

    def manage_getSysPath(self):
        return sorted(sys.path)

    def manage_getConfiguration(self):
        config_results = []
        config = getConfiguration()

        try:
            keys = config.getSectionAttributes()
        except AttributeError:
            # This happens in unit tests with a DefaultConfiguration object
            keys = config.__dict__.keys()

        for key in keys:

            # Databases are visible on the Database Chooser already
            if key == 'databases':
                continue

            config_results.append({'name': key,
                                   'value': str(getattr(config, key))})
        return config_results


InitializeClass(ConfigurationViewer)


class ApplicationManager(Persistent, Tabs, Traversable, Implicit):
    """System management
    """
    __allow_access_to_unprotected_subobjects__ = 1
    __roles__ = ('Manager',)

    id = 'Control_Panel'
    name = title = 'Control Panel'
    meta_type = 'Control Panel'
    zmi_icon = 'fa fa-cog'
    process_start = int(time.time())

    Database = DatabaseChooser()
    Configuration = ConfigurationViewer()
    DavLocks = DavLockManager()

    manage = manage_main = DTMLFile('dtml/cpContents', globals())
    manage_main._setName('manage_main')
    manage_options = (
        {'label': 'Control Panel', 'action': 'manage_main'},
        {'label': 'Databases', 'action': 'Database/manage_main'},
        {'label': 'Configuration', 'action': 'Configuration/manage_main'},
        {'label': 'DAV Locks', 'action': 'DavLocks/manage_main'},
    )
    MANAGE_TABS_NO_BANNER = True

    def version_txt(self):
        if not hasattr(self, '_v_version_txt'):
            self._v_version_txt = version_txt()

        return self._v_version_txt

    def process_id(self):
        return os.getpid()

    def process_time(self, _when=None):
        if _when is None:
            _when = time.time()
        s = int(_when) - self.process_start
        d = int(s / 86400)
        s = s - (d * 86400)
        h = int(s / 3600)
        s = s - (h * 3600)
        m = int(s / 60)
        s = s - (m * 60)
        d = d and ('%d day%s' % (d, (d != 1 and 's' or ''))) or ''
        h = h and ('%d hour%s' % (h, (h != 1 and 's' or ''))) or ''
        m = m and ('%d min' % m) or ''
        s = '%d sec' % s
        return '%s %s %s %s' % (d, h, m, s)

    def sys_version(self):
        return sys.version

    def sys_platform(self):
        return sys.platform

    def debug_mode(self):
        return getConfiguration().debug_mode

    def getINSTANCE_HOME(self):
        return getConfiguration().instancehome

    def getCLIENT_HOME(self):
        return getConfiguration().clienthome


class AltDatabaseManager(Traversable, UndoSupport):
    """ Database management DBTab-style
    """
    id = 'DatabaseManagement'
    name = title = 'Database Management'
    meta_type = 'Database Management'

    manage = manage_main = DTMLFile('dtml/dbMain', globals())
    manage_main._setName('manage_main')
    manage_options = (
        {'label': 'Control Panel', 'action': '../../manage_main'},
        {'label': 'Databases', 'action': '../manage_main'},
        {'label': 'Database', 'action': 'manage_main'},
    ) + UndoSupport.manage_options
    MANAGE_TABS_NO_BANNER = True

    def _getDB(self):
        return self._p_jar.db()

    def cache_length(self):
        return self._getDB().cacheSize()

    def cache_length_bytes(self):
        return self._getDB().getCacheSizeBytes()

    def cache_detail_length(self):
        return self._getDB().cacheDetailSize()

    def cache_size(self):
        db = self._getDB()
        return db.getCacheSize()

    def database_size(self):
        return self._getDB().objectCount()

    def db_name(self):
        return self._getDB().getName()

    def db_size(self):
        s = self._getDB().getSize()
        if isinstance(s, str):
            return s

        if s >= 1048576.0:
            return '%.1fM' % (s / 1048576.0)
        return '%.1fK' % (s / 1024.0)

    @requestmethod('POST')
    def manage_minimize(self, value=1, REQUEST=None):
        "Perform a full sweep through the cache"
        # XXX Add a deprecation warning about value?
        self._getDB().cacheMinimize()

        if REQUEST is not None:
            msg = 'ZODB in-memory caches minimized.'
            url = '%s/manage_main?manage_tabs_message=%s' % (REQUEST['URL1'],
                                                             msg)
            REQUEST.RESPONSE.redirect(url)

    @requestmethod('POST')
    def manage_pack(self, days=0, REQUEST=None):
        """Pack the database"""
        if not isinstance(days, (int, float)):
            try:
                days = float(days)
            except ValueError:
                days = None

        if days is not None:
            t = time.time() - (days * 86400)
            self._getDB().pack(t)
            msg = 'Database packed to %s days' % str(days)
        else:
            t = None
            msg = 'Invalid days value %s' % str(days)

        if REQUEST is not None:
            url = '%s/manage_main?manage_tabs_message=%s' % (REQUEST['URL1'],
                                                             msg)
            REQUEST['RESPONSE'].redirect(url)

        return t


InitializeClass(AltDatabaseManager)
