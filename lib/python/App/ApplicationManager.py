__doc__="""System management components"""
__version__='$Revision: 1.36 $'[11:-2]


import sys,os,time,string,Globals, Acquisition
from Globals import HTMLFile
from OFS.ObjectManager import ObjectManager
from OFS.Folder import Folder
from CacheManager import CacheManager
from OFS import SimpleItem
from App.Dialogs import MessageDialog
from Product import ProductFolder

class Fake:
    def locked_in_session(self): return 0

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
    

class ApplicationManager(Folder,CacheManager):
    """System management"""

    __roles__=['Manager']
    isPrincipiaFolderish=1
    Database=DatabaseManager()

    manage=manage_main=HTMLFile('cpContents', globals())
    manage_undoForm=HTMLFile('undo', globals())

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

    def parentObject(self):
	try:    return (self.aq_parent,)
	except: return ()

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

    def db_name(self): return Globals.Bobobase._jar.db.file_name

    def db_size(self):
        s=os.stat(self.db_name())[6]
	if s >= 1048576.0: return '%.1fM' % (s/1048576.0)
        return '%.1fK' % (s/1024.0)

    def manage_shutdown(self):
        """Shut down the application"""
	db=Globals.Bobobase._jar.db
	db.save_index()
	db.file.close()
	db=Globals.SessionBase.TDB
	db.save_index()
	db.file.close()
	sys.exit(0)

    def manage_pack(self, days=0, REQUEST=None):
	"""Pack the database"""
	if self._p_jar.db is not Globals.Bobobase._jar.db:
	    raise 'Session Error', (
		'''You may not pack the application database while
		working in a <em>session</em>''')
        t=time.time()-days*86400
        if Globals.Bobobase.has_key('_pack_time'):
            since=Globals.Bobobase['_pack_time']
            if t <= since:
                if REQUEST: return self.manage_main(self, REQUEST)
                return

        Globals.Bobobase['_pack_time']=t
        get_transaction().note('')
        get_transaction().commit()
	Globals.Bobobase._jar.db.pack(t,0)
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

