##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__="""System management components"""

__version__='$Revision: 1.94 $'[11:-2]

import sys,os,time,Globals, Acquisition, os, Undo
from Globals import DTMLFile
from OFS.ObjectManager import ObjectManager
from OFS.Folder import Folder
from CacheManager import CacheManager
from DavLockManager import DavLockManager
from DateTime.DateTime import DateTime
from OFS import SimpleItem
from App.config import getConfiguration
from App.Dialogs import MessageDialog
from Product import ProductFolder
from version_txt import version_txt
from cStringIO import StringIO
from AccessControl import getSecurityManager
from zExceptions import Redirect
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from cgi import escape
import zLOG
import Lifetime

try: import thread
except: get_ident=lambda: 0
else: get_ident=thread.get_ident

class Fake:
    def locked_in_version(self): return 0

class DatabaseManager(Fake, SimpleItem.Item, Acquisition.Implicit):
    """Database management (legacy) """
    manage=manage_main=DTMLFile('dtml/dbMain', globals())
    manage_main._setName('manage_main')
    id        ='DatabaseManagement'
    name=title='Database Management'
    meta_type ='Database Management'
    icon='p_/DatabaseManagement_icon'

    manage_options=(
        (
        {'label':'Database', 'action':'manage_main',
         'help':('OFSP','Database-Management_Database.stx')},
        {'label':'Activity', 'action':'manage_activity',
         'help':('OFSP','Database-Management_Activity.stx')},
        {'label':'Cache Parameters', 'action':'manage_cacheParameters',
         'help':('OFSP','Database-Management_Cache-Parameters.stx')},
        {'label':'Flush Cache', 'action':'manage_cacheGC',
         'help':('OFSP','Database-Management_Flush-Cache.stx')},
        )
        )

    # These need to be here rather to make tabs work correctly. This
    # needs to be revisited.
    manage_activity=Globals.DTMLFile('dtml/activity', globals())
    manage_cacheParameters=Globals.DTMLFile('dtml/cacheParameters', globals())
    manage_cacheGC=Globals.DTMLFile('dtml/cacheGC', globals())


Globals.default__class_init__(DatabaseManager)

class FakeConnection:
    # Supports the methods of Connection that CacheManager needs

    def __init__(self, db, parent_jar):
        self._db = db
        self.version = parent_jar.getVersion()

    def db(self):
        return self._db

    def getVersion(self):
        return self.version

class DatabaseChooser (SimpleItem.SimpleItem):
    """Lets you choose which database to view
    """
    meta_type = 'Database Management'
    name = title = 'Database Management'
    icon = 'p_/DatabaseManagement_icon'
    isPrincipiaFolderish = 1

    manage_options=(
        {'label':'Databases', 'action':'manage_main'},
        )

    manage_main = PageTemplateFile('www/chooseDatabase.pt', globals())

    def __init__(self, id):
        self.id = id

    def getDatabaseNames(self):
        configuration = getConfiguration()
        names = configuration.dbtab.listDatabaseNames()
        names.sort()
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

Globals.InitializeClass(DatabaseChooser)


class VersionManager(Fake, SimpleItem.Item, Acquisition.Implicit):
    """Version management"""
    manage=manage_main=DTMLFile('dtml/versionManager', globals())
    manage_main._setName('manage_main')
    id        ='Versions'
    name=title='Version Management'
    meta_type ='Version Management'
    icon='p_/VersionManagement_icon'

    manage_options=(
        (
        {'label':'Version', 'action':'manage_main',
         'help':('OFSP','Version-Management_Version.stx')},
        )
        )

Globals.default__class_init__(VersionManager)




# refcount snapshot info
_v_rcs=None
_v_rst=None

class DebugManager(Fake, SimpleItem.Item, Acquisition.Implicit):
    """Debug and profiling information"""
    manage=manage_main=DTMLFile('dtml/debug', globals())
    manage_main._setName('manage_main')
    id        ='DebugInfo'
    name=title='Debug Information'
    meta_type = name
    icon='p_/DebugManager_icon'

    manage_options=(
        (  {'label':'Debugging Info', 'action':'manage_main',
            'help':('OFSP','Debug-Information_Debug.stx')},
           {'label':'Profiling', 'action':'manage_profile',
            'help':('OFSP','Debug-Information_Profile.stx')},
           )
        )

    manage_debug=DTMLFile('dtml/debug', globals())

    def refcount(self, n=None, t=(type(Fake), type(Acquisition.Implicit))):
        # return class reference info
        dict={}
        for m in sys.modules.values():
            for sym in dir(m):
                ob=getattr(m, sym)
                if type(ob) in t:
                    dict[ob]=sys.getrefcount(ob)
        pairs=[]
        append=pairs.append
        for ob, v in dict.items():
            if hasattr(ob, '__module__'):
                name='%s.%s' % (ob.__module__, ob.__name__)
            else: name='%s' % ob.__name__
            append((v, name))
        pairs.sort()
        pairs.reverse()
        if n is not None:
            pairs=pairs[:n]
        return pairs

    def refdict(self):
        rc=self.refcount()
        dict={}
        for v, n in rc:
            dict[n]=v
        return dict

    def rcsnapshot(self):
        global _v_rcs
        global _v_rst
        _v_rcs=self.refdict()
        _v_rst=DateTime()

    def rcdate(self):
        return _v_rst

    def rcdeltas(self):
        if _v_rcs is None:
            self.rcsnapshot()
        nc=self.refdict()
        rc=_v_rcs
        rd=[]
        for n, c in nc.items():
            try:
                prev=rc[n]
                if c > prev:
                    rd.append( (c - prev, (c, prev, n)) )
            except: pass
        rd.sort()
        rd.reverse()
        return map(lambda n: {'name': n[1][2],
                              'delta': n[0],
                              'pc': n[1][1],
                              'rc': n[1][0]}, rd)

    def dbconnections(self):
        return Globals.DB.connectionDebugInfo()


    # Profiling support

    manage_profile=DTMLFile('dtml/profile', globals())

    def manage_profile_stats(self, sort='time', limit=200, stripDirs=1, mode='stats'):
        """Return profile data if available"""
        stats=getattr(sys, '_ps_', None)
        if stats is None:
            return None
        output=StringIO()
        stdout=sys.stdout
        if stripDirs:
            from copy import copy; stats= copy(stats)
            stats.strip_dirs()
        stats.sort_stats(sort)
        sys.stdout=output
        getattr(stats,'print_%s' % mode)(limit)
        sys.stdout.flush()
        sys.stdout=stdout
        return output.getvalue()

    def manage_getSysPath(self):
        return list(sys.path)

Globals.default__class_init__(DebugManager)




class ApplicationManager(Folder,CacheManager):
    """System management"""

    __roles__=('Manager',)
    isPrincipiaFolderish=1
    Database= DatabaseChooser('Database') #DatabaseManager()
    Versions= VersionManager()
    DebugInfo=DebugManager()
    DavLocks = DavLockManager()

    manage=manage_main=DTMLFile('dtml/cpContents', globals())
    manage_main._setName('manage_main')

    def version_txt(self):
        if not hasattr(self, '_v_version_txt'):
            self._v_version_txt=version_txt()

        return self._v_version_txt

    def sys_version(self): return sys.version
    def sys_platform(self): return sys.platform

    _objects=(
        {'id': 'Database',
         'meta_type': Database.meta_type},
        {'id': 'Versions',
         'meta_type': Versions.meta_type},
        {'id': 'DavLocks',
         'meta_type': DavLocks.meta_type},
        {'id': 'Products',
         'meta_type': 'Product Management'},
        {'id': 'DebugInfo',
         'meta_type': DebugInfo.meta_type},
        )

    manage_options=(
        (
        {'label':'Contents', 'action':'manage_main',
         'help':('OFSP','Control-Panel_Contents.stx')},
        )
        +Undo.UndoSupport.manage_options
        )

    id        ='Control_Panel'
    name=title='Control Panel'
    meta_type ='Control Panel'
    icon='p_/ControlPanel_icon'

    process_id=os.getpid()
    process_start=int(time.time())

    # Disable some inappropriate operations
    manage_addObject=None
    manage_delObjects=None
    manage_addProperty=None
    manage_editProperties=None
    manage_delProperties=None

    def __init__(self):
        self.Products=ProductFolder()


# Note by brian:
#
# This __setstate__ does not seem to work - it creates a new ProductFolder
# and adds it to the CP instance if needed, but the resulting PF does not
# seem to be persistent ;( Rather than spend much time figuring out why,
# I just added a check in Application.open_bobobase to create the PF if
# it is needed (this is where several other b/c checks are done anyway.)
#
#
#    def __setstate__(self, v):
#        ApplicationManager.inheritedAttribute('__setstate__')(self, v)
#        if not hasattr(self, 'Products'):
#            self.Products=ProductFolder()


    def _canCopy(self, op=0):
        return 0

    def _init(self):
        pass

    def manage_app(self, URL2):
        """Return to the main management screen"""
        raise Redirect, URL2+'/manage'

    def process_time(self):
        s=int(time.time())-self.process_start
        d=int(s/86400)
        s=s-(d*86400)
        h=int(s/3600)
        s=s-(h*3600)
        m=int(s/60)
        s=s-(m*60)
        d=d and ('%d day%s'  % (d, (d != 1 and 's' or ''))) or ''
        h=h and ('%d hour%s' % (h, (h != 1 and 's' or ''))) or ''
        m=m and ('%d min' % m) or ''
        s='%d sec' % s
        return '%s %s %s %s' % (d, h, m, s)

    def thread_get_ident(self): return get_ident()

    def db_name(self):
        return self._p_jar.db().getName()

    def db_size(self):
        s=self._p_jar.db().getSize()
        if type(s) is type(''):
            return s

        if s >= 1048576.0: return '%.1fM' % (s/1048576.0)
        return '%.1fK' % (s/1024.0)

    if os.environ.has_key('ZMANAGED'):
        manage_restartable=1
        def manage_restart(self, URL1):
            """Shut down the application"""
            try:
                user = '"%s"' % getSecurityManager().getUser().getUserName()
            except:
                user = 'unknown user'
            zLOG.LOG("ApplicationManager", zLOG.INFO,
                     "Restart requested by %s" % user)
            #for db in Globals.opened: db.close()
            Lifetime.shutdown(1)
            return """<html>
            <head><meta HTTP-EQUIV=REFRESH CONTENT="10; URL=%s/manage_main">
            </head>
            <body>Zope is restarting</body></html>
            """ % escape(URL1, 1)

    def manage_shutdown(self):
        """Shut down the application"""
        try:
            user = '"%s"' % getSecurityManager().getUser().getUserName()
        except:
            user = 'unknown user'
        zLOG.LOG("ApplicationManager", zLOG.INFO,
                 "Shutdown requested by %s" % user)
        #for db in Globals.opened: db.close()
        Lifetime.shutdown(0)
        return """<html>
        <head>
        </head>
        <body>Zope is shutting down</body></html>
        """

    def manage_pack(self, days=0, REQUEST=None):
        """Pack the database"""

        t=time.time()-days*86400

        db=self._p_jar.db()
        t=db.pack(t)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(
                REQUEST['URL1']+'/manage_workspace')
        return t

    def revert_points(self): return ()

    def version_list(self):
        # Return a list of currently installed products/versions
        path_join=os.path.join
        isdir=os.path.isdir
        exists=os.path.exists

        cfg = getConfiguration()
        product_dir=path_join(cfg.softwarehome,'Products')
        product_names=os.listdir(product_dir)
        product_names.sort()
        info=[]
        for product_name in product_names:
            package_dir=path_join(product_dir, product_name)
            if not isdir(package_dir):
                continue
            version_txt = None
            for name in ('VERSION.TXT', 'VERSION.txt', 'version.txt'):
                v = path_join(package_dir, name)
                if exists(v):
                    version_txt = v
                    break
            if version_txt is not None:
                file=open(version_txt, 'r')
                data=file.readline()
                file.close()
                info.append(data.strip())
        return info


    def version_info(self):
        r=[]
        try: db=self._p_jar.db()
        except: raise ValueError, """
        Sorry, <em>Version management</em> is only supported if you use ZODB 3.
        """
        for v in db.versions():
            if db.versionEmpty(v): continue
            r.append({'id': v})
        return r

    def manage_saveVersions(self, versions, REQUEST=None):
        "Commit some versions"
        db=self._p_jar.db()
        for v in versions:
            db.commitVersion(v)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(REQUEST['URL1']+'/manage_main')

    def manage_discardVersions(self, versions, REQUEST=None):
        "Discard some versions"
        db=self._p_jar.db()
        for v in versions:
            db.abortVersion(v)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(REQUEST['URL1']+'/manage_main')

    def getSOFTWARE_HOME(self):
        return getConfiguration().softwarehome

    def getZOPE_HOME(self):
        return getConfiguration().zopehome

    def getINSTANCE_HOME(self):
        return getConfiguration().instancehome

    def getCLIENT_HOME(self):
        return getConfiguration().clienthome

    def getServers(self):
        # used only for display purposes
        # return a sequence of two-tuples.  The first element of
        # each tuple is the service name, the second is a string repr. of
        # the port/socket/other on which it listens
        from asyncore import socket_map
        l = []
        for k,v in socket_map.items():
            # this is only an approximation
            if hasattr(v, 'port'):
                type = str(getattr(v, '__class__', 'unknown'))
                port = v.port
                l.append((str(type), 'Port: %s' % port))
        return l

    def objectIds(self, spec=None):
        """ this is a patch for pre-2.4 Zope installations. Such
            installations don't have an entry for the WebDAV LockManager
            introduced in 2.4.
        """

        meta_types = map(lambda x: x.get('meta_type',None) , self._objects)

        if not self.DavLocks.meta_type in meta_types:

            lst = list(self._objects)
            lst.append(  {'id': 'DavLocks', \
                'meta_type': self.DavLocks.meta_type})
            self._objects = tuple(lst)

        return Folder.objectIds(self, spec)

class AltDatabaseManager(DatabaseManager, CacheManager):
    """Database management DBTab-style
    """
    db_name = ApplicationManager.db_name.im_func
    db_size = ApplicationManager.db_size.im_func
    manage_pack = ApplicationManager.manage_pack.im_func

