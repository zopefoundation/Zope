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
__doc__="""System management components"""
__version__='$Revision: 1.45 $'[11:-2]


import sys,os,time,string,Globals, Acquisition
from Globals import HTMLFile
from OFS.ObjectManager import ObjectManager
from OFS.Folder import Folder
from CacheManager import CacheManager
from OFS import SimpleItem
from App.Dialogs import MessageDialog
from Product import ProductFolder

class Fake:
    def locked_in_version(self): return 0

class DatabaseManager(Fake, SimpleItem.Item, Acquisition.Implicit):
    """Database management"""
    manage=manage_main=HTMLFile('dbMain', globals())
    id        ='DatabaseManagement'
    name=title='Database Management'
    meta_type ='Database Management'
    icon='p_/DatabaseManagement_icon'

    manage_options=(
        {'label':'Database', 'action':'manage_main'},
        {'label':'Cache Parameters', 'action':'manage_cacheParameters'},
        {'label':'Flush Cache', 'action':'manage_cacheGC'},
        {'label':'Undo', 'action':'manage_UndoForm'},
        )
    

def version_txt():
    try: return open(os.path.join(SOFTWARE_HOME,'version.txt')).read()
    except: return '(unreleased version)'
        
    return self._v_version_txt

class ApplicationManager(Folder,CacheManager):
    """System management"""

    __roles__=['Manager']
    isPrincipiaFolderish=1
    Database=DatabaseManager()

    manage=manage_main=HTMLFile('cpContents', globals())
    manage_undoForm=HTMLFile('undo', globals())

    def version_txt(self):
        if not hasattr(self, '_v_version_txt'):
            self._v_version_txt=version_txt()
                
        return self._v_version_txt

    def sys_version(self): return sys.version
    def sys_platform(self): return sys.platform

    _objects=(
        {'id': 'Database',
         'meta_type': Database.meta_type},
        {'id': 'Products',
         'meta_type': 'Product Management'},
        )

    manage_options=(
        {'label':'Contents', 'action':'manage_main'},
        {'label':'Undo', 'action':'manage_UndoForm'},
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
        raise 'Redirect', URL2+'/manage'

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

    def db_name(self):
        try: db=self._p_jar.db()
        except:
            # BoboPOS 2
            return Globals.BobobaseName
        else:
            # ZODB 3
            return db.getName()

    def db_size(self):
        s=os.stat(self.db_name())[6]
        if s >= 1048576.0: return '%.1fM' % (s/1048576.0)
        return '%.1fK' % (s/1024.0)

    def manage_shutdown(self):
        """Shut down the application"""
        for db in Globals.opened: db.close()
        sys.exit(0)

    def manage_pack(self, days=0, REQUEST=None):
        """Pack the database"""

        t=time.time()-days*86400

        try: db=self._p_jar.db()
        except: pass
        else: return db.pack(t)

        # BoboPOS2:
        if self._p_jar.db is not Globals.Bobobase._jar.db:
            raise 'Version Error', (
                '''You may not pack the application database while
                working in a <em>version</em>''')
        if Globals.Bobobase.has_key('_pack_time'):
            since=Globals.Bobobase['_pack_time']
            if t <= since:
                if REQUEST: return self.manage_main(self, REQUEST)
                return

        # This is a little cheesy.  We really should record the pack
        # time first, but we may need to pack to have space to
        # record the information.
        Globals.Bobobase._jar.db.pack(t,0)
        Globals.Bobobase['_pack_time']=t
        get_transaction().note('')
        get_transaction().commit()
        if REQUEST: return self.manage_main(self, REQUEST)

    def revert_points(self): return ()

    def version_list(self):
        # Return a list of currently installed products/versions
        path_join=os.path.join
        isdir=os.path.isdir
        exists=os.path.exists
        strip=string.strip

        product_dir=path_join(SOFTWARE_HOME,'Products')
        product_names=os.listdir(product_dir)
        product_names.sort()
        info=[]
        for product_name in product_names:
            package_dir=path_join(product_dir, product_name)
            if not isdir(package_dir):
                continue
            version_txt=path_join(package_dir, 'version.txt')
            if not exists(version_txt):
                continue
            file=open(version_txt, 'r')
            data=file.readline()
            file.close()
            info.append(strip(data))
        return info

