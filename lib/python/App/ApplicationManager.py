__doc__="""System management components"""
__version__='$Revision: 1.21 $'[11:-2]


import sys,os,time,Globals
from Globals import HTMLFile
from OFS.ObjectManager import ObjectManager
from CacheManager import CacheManager
from OFS import SimpleItem

class ApplicationManager(ObjectManager,SimpleItem.Item,CacheManager):
    """System management"""
    __roles__=['Manager,',]

    manage=manage_main=HTMLFile('appMain', globals())
    manage_packForm=HTMLFile('pack', globals())
    manage_undoForm=HTMLFile('undo', globals())
    manage=manage_main

    manage_options=(
    {'icon':'OFS/ControlPanel_icon.gif', 'label':'System',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'App/CacheManager_icon.gif','label':'Cache',
     'action':'manage_cacheForm','target':'manage_main'},
    {'icon':'App/undo_icon.gif', 'label':'Undo',
     'action':'manage_UndoForm',   'target':'manage_main'},
#    {'icon':'OFS/Help_icon.gif', 'label':'Help',
#     'action':'manage_main',   'target':'_new'},
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
    isPrincipiaFolderish=0

    def copyToClipboard(self, REQUEST):
	return Globals.MessageDialog(title='Not Supported',
				     message='This item cannot be copied',
				     action ='./manage_main',)

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
        m=int((s-(h*3600))/60)
        d=d and ('%s day%s'  % (d,(d!=1 and 's' or ''))) or ''
        return '%s %02d:%02d' % (d,h,m)

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

    def manage_pack(self, days=0, REQUEST):
	"""Pack the database"""
	if self._p_jar.db is not Globals.Bobobase._jar.db:
	    raise 'Session Error', (
		'''You may not pack the application database while
		working in a <em>session</em>''')
	Globals.Bobobase._jar.db.pack(time.time()-days*86400,1)
	return self.manage_main(self, REQUEST)

    def revert_points(self): return ()

    def manage_addProduct(self, product):
	"""Register a product
	"""
	products=Globals.Bobobase['products']
	if product not in products:
	    Globals.Bobobase['products']=tuple(products)+(product,)
