__doc__="""System management components"""
__version__='$Revision: 1.27 $'[11:-2]


import sys,os,time,string,Globals
from Globals import HTMLFile
from OFS.ObjectManager import ObjectManager
from CacheManager import CacheManager
from OFS import SimpleItem
from App.Dialogs import MessageDialog


class ApplicationManager(ObjectManager,SimpleItem.Item,CacheManager):
    """System management"""
    __roles__=['Manager']

    manage=manage_main=HTMLFile('appMain', globals())
    manage_undoForm=HTMLFile('undo', globals())

    manage_options=(
    {'icon':'OFS/ControlPanel_icon.gif', 'label':'System',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'App/CacheManager_icon.gif','label':'Cache',
     'action':'manage_cacheForm','target':'manage_main'},
    {'icon':'App/undo_icon.gif', 'label':'Undo',
     'action':'manage_UndoForm',   'target':'manage_main'},
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
	Globals.Bobobase._jar.db.pack(time.time()-days*86400,0)
	if REQUEST: return self.manage_main(self, REQUEST)

    def revert_points(self): return ()

    createProductEncyclopedia__roles__=()
    def createProductEncyclopedia(self, product, format=None, RESPONSE=None):
	"""Create product encyclopedia files

	In StructuredText, HTML, and MML formats.
	"""
	if type(product) is not type([]): product=(product,)
	import PrincipiaHelp.product_encyclopedia
	for p in product:
	    r=PrincipiaHelp.product_encyclopedia.doc(p, format, RESPONSE)
	if r is not None: return r
	return MessageDialog(message='Documented: %s' % product)

    def version_list(self):
	# Return a list of currently installed products/versions
	path_join=os.path.join
	isdir=os.path.isdir
	exists=os.path.exists
	split=string.split
	strip=string.strip
	join =string.join

	product_dir=path_join(SOFTWARE_HOME,'lib/python/Products')
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
	    v=split(strip(data), '-')
	    if len(v) != 4:
		continue
	    if v[0]=='OFSP':
		v[0]='Principia'
	    info.append('%s %s.%s.%s' % (v[0], v[1], v[2], v[3]))
	return info

