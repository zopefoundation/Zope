from OFS import Folder
import Globals, string, OFS.SimpleItem, Acquisition, AccessControl.Role
from ZPublisher.mapply import mapply
from Manage_Options import Manage_Options
from Ac_Permissions import Ac_Permissions
from ExtensionClass import Base
from App.FactoryDispatcher import FactoryDispatcher

class Item(OFS.SimpleItem.Item,
           Globals.Persistent,
           Acquisition.Implicit,
           AccessControl.Role.RoleManager,
           ):
    """Basic instances
    """

    manage_options=(
	{'label':'Security',   'action':'manage_access'},
	)
 
    __ac_permissions__=(
	('View management screens', ('manage_tabs',)),
	('Change permissions',      ('manage_access',)           ),
	)

builtins=(
    ('OFS.Folder Folder', 'Zope Folder', Folder.Folder),
    ('OFS.SimpleItem Item', 'Minimal Item', Item),
    )
builtin_classes={}
builtin_names={}
for id, name, c in builtins:
    builtin_classes[id]=c
    builtin_names[id]=name

class PersistentClass(Base):
    def __class_init__(self): pass



manage_addZClassForm=Globals.HTMLFile(
    'addZClass', globals(), default_class_='OFS.SimpleItem Item')

def manage_addZClass(self, id, title='', base=[], REQUEST=None):
    """Add a Z Class
    """
    if not base: base=('OFS.SimpleItem Item',)
    bases=[PersistentClass]
    for b in base:
        if builtin_classes.has_key(b): bases.append(builtin_classes[b])
        else:                          bases.append(getattr(self, b)._zclass_)

    bases=tuple(bases)
    
    self._setObject(id, ZClass(id,title,bases))
    if REQUEST is not None: return self.manage_main(self,REQUEST)

def manage_subclassableClassNames(self):
    r={}
    r.update(builtin_names)

    while 1:
        if not hasattr(self, 'objectItems'): break
        for k, v in self.objectItems():
            if hasattr(v,'_zclass_') and not r.has_key(k):
                r[k]=v.title_and_id()
        if not hasattr(self, 'aq_parent'): break
        self=self.aq_parent
                
    r=r.items()
    r.sort()
    return r

class Template:
    _p_oid=_p_jar=__module__=None
    _p_changed=0
    icon=''
    
class ZClass(Folder.Folder):
    """Zope Class
    """
    meta_type="Z Class"
    icon=""
    instance__meta_type='instance'
    instance__icon=''

    _properties=({'id':'title', 'type': 'string'},
                 {'id':'instance__meta_type', 'type': 'string'},
                 {'id':'instance__icon', 'type': 'string'},
                 )

    _objects=(
        {'id': 'instance__manage_options',
         'meta_type': Manage_Options.meta_type},
        {'id': 'instance____ac_permissions__',
         'meta_type': Ac_Permissions.meta_type},
        )

    manage_main=Globals.HTMLFile('contents', globals())

    def all_meta_types(self):
        return ZClass.inheritedAttribute('all_meta_types')(self)+(
            {'name': 'Instance icon',
             'action':'manage_addInstanceIconForm'},
            )
    

    def __init__(self, id, title, bases):
        self.id=id
        self.title=title
        dict={}
        dict.update(Template.__dict__)
        dict['__doc__']=dict['meta_type']=self.instance__meta_type=title or id
        self._zclass_=c=type(bases[0])(id, bases, dict)
        self.instance__manage_options=c.manage_options=Manage_Options()
        self.instance____ac_permissions__=c.__ac_permissions__=Ac_Permissions()

    def index_html(self, id, REQUEST):
        """Create Z instance
        """
        i=mapply(self._zclass_, (), REQUEST)
        if not hasattr(i, 'id'): i.id=id

        folder=durl=None
        if hasattr(self, 'Destination'):
            try:
                d=self.Destination
                if d.im_self.__class__ is FactoryDispatcher:
                    folder=d()
                    durl=self.DestinationURL()
            except: pass
        if folder is None: folder=self.aq_parent

        folder._setObject(id, i)

        if REQUEST.has_key('RESPONSE'):
            if durl is None: durl=REQUEST['URL2']
            REQUEST['RESPONSE'].redirect(durl+'/manage_workspace')

    def propertyLabel(self, id):
        """Return a label for the given property id
        """
        if id[:10]=='instance__': return id[10:]
        return id

    def _setProperty(self, id, value, type='string'):
        return ZClass.inheritedAttribute('_setProperty')(
            self, 'instance__'+id, value, type)

    def _setPropValue(self, id, value):
        setattr(self,id,value)
        z=self._zclass_
        setattr(z, id[10:], value)
        z._p_changed=1
        get_transaction().register(z)
        
    def _delPropValue(self, id):
        delattr(self,id)
        z=self._zclass_
        delattr(z, id[10:])
        z._p_changed=1
        get_transaction().register(z)



    def _setObject(self,id,object,*whatever):
        ZClass.inheritedAttribute('_setObject')(self, 'instance__'+id, object)

    _reserved=()
    def _setOb(self, id, object):
	if id in self._reserved: 
	    raise 'Input Error', 'The id %s is reserved' % id
        setattr(self, id, object)
        z=self._zclass_
        setattr(z, id[10:], object)
        z._p_changed=1
        get_transaction().register(z)

    def _delOb(self, id):
        delattr(self, id)
        z=self._zclass_
        delattr(z, id[10:])
        z._p_changed=1
        get_transaction().register(z)

    def all_methods(self):
        r={}
        for id in self.objectIds():
            id=id[10:]
            if id in ('manage_options','__ac_permissions__'):
                continue
            r[id]=1

        perms=self._zclass_.inheritedAttribute('__ac_permissions__')
        if hasattr(perms,'im_func'): perms=perms.im_func # Waaa
        for pname, methods in perms:
            for id in methods:
                if id: r[id]=1

        r=r.keys()
        r.sort()
        return r

    manage_addInstanceIconForm=Globals.HTMLFile('addIcon',globals())
    def manage_addInstanceIcon(self, id, title, file, REQUEST):
        " "
        id=self.manage_addImage(id, file, title)
        s=REQUEST['BASE1']
        self.manage_changeProperties(
            instance__icon=REQUEST['URL1'][len(s)+1:]+'/instance__'+id)
        return self.manage_main(self,REQUEST)
        

    def manage_addDTMLMethod(self, id, title='', file='',
                             REQUEST=None, submit=None):
        if not file: file=default_dm_html
        return self.inheritedAttribute('manage_addDTMLMethod')(
            self, id, title, file, REQUEST, submit)

default_dm_html="""<html>
<head><title><!--#var document_title--></title></head>
<body bgcolor="#FFFFFF" LINK="#000099" VLINK="#555555">
<!--#var manage_tabs-->

<P>This is the <!--#var document_id--> Document in 
the <!--#var title_and_id--> Folder.</P>

</body></html>
"""
