"""Document object"""

__version__='$Revision: 1.44 $'[11:-2]

from Globals import HTML, HTMLFile, MessageDialog
from string import join,split,strip,rfind,atoi
from AccessControl.Role import RoleManager
from SimpleItem import Item_w__name__
from Acquisition import Explicit
import regex, Globals


class Document(HTML, Explicit, RoleManager, Item_w__name__):
    """ """
    meta_type='Document'
    icon     ='p_/doc'
    _proxy_roles=()



    # Documents masquerade as functions:
    class func_code: pass
    func_code=func_code()
    func_code.co_varnames='self','REQUEST','RESPONSE'
    func_code.co_argcount=3

    manage_options=({'label':'Edit', 'action':'manage_main',
		     'target':'manage_main',
	            },
		    {'label':'Upload', 'action':'manage_uploadForm',
		     'target':'manage_main',
		    },
		    {'label':'View', 'action':'',
		     'target':'manage_main',
		    },
		    {'label':'Proxy', 'action':'manage_proxyForm',
		     'target':'manage_main',
		    },
		    {'label':'Security', 'action':'manage_access',
		     'target':'manage_main',
		    },
		   )

    __ac_permissions__=(
    ('View management screens',
     ['manage','manage_tabs','manage_uploadForm']),
    ('Change permissions', ['manage_access']),
    ('Change/upload data', ['manage_edit','manage_upload','PUT']),
    ('Change proxy roles', ['manage_proxyForm','manage_proxy']),
    ('View', ['__call__',]),
    ('Shared permission', ['',]),
    )

    __state_names__=(
	HTML.__state_names__+('title', '_proxy_roles')+
	tuple(reduce(lambda a, b:
		     a+b,
		     map(lambda permission:
			 map(lambda name:
			     name+'__roles__',
			     permission[1]
			     ),
			 __ac_permissions__
			 )
		     ))
	)
	   

    __call____roles__='Manager', 'Shared'
    def __call__(self, client=None, REQUEST={}, RESPONSE=None, **kw):
	""" """
	kw['document_id']   =self.id
        kw['document_title']=self.title
	r=apply(HTML.__call__, (self, client, REQUEST), kw)
	if RESPONSE is None: return r
	return decapitate(r, RESPONSE)

    def validate(self, inst, parent, name, value, md):
	if hasattr(value, '__roles__'):
	    roles=value.__roles__
	elif inst is parent:
	    return 1
	else:
	    # if str(name)[:6]=='manage': return 0
	    if hasattr(parent,'__roles__'):
		roles=parent.__roles__
	    elif hasattr(parent, 'aq_acquire'):
		try: roles=parent.aq_acquire('__roles__')
		except AttributeError: return 0
	    else: return 0
	    value=parent
	if roles is None: return 1

	try: 
	    if md.AUTHENTICATED_USER.hasRole(value, roles):
		return 1
	except AttributeError: pass

	for r in self._proxy_roles:
	    if r in roles: return 1

	return 0

    manage_editForm=HTMLFile('documentEdit', globals())
    manage_uploadForm=HTMLFile('documentUpload', globals())
    manage=manage_main=manage_editDocument=manage_editForm
    manage_proxyForm=HTMLFile('documentProxy', globals())

    def manage_edit(self,data,title,SUBMIT='Change',dtpref_cols='50',
		    dtpref_rows='20',REQUEST=None):
	""" """
	self._validateProxy(REQUEST)
        if SUBMIT=='Smaller':
            rows=atoi(dtpref_rows)-5
            cols=atoi(dtpref_cols)-5
	    e='Friday, 31-Dec-99 23:59:59 GMT'
	    resp=REQUEST['RESPONSE']
	    resp.setCookie('dtpref_rows',str(rows),path='/',expires=e)
	    resp.setCookie('dtpref_cols',str(cols),path='/',expires=e)
	    return self.manage_main(self,REQUEST,title=title,__str__=data,
				    dtpref_cols=cols,dtpref_rows=rows)
        if SUBMIT=='Bigger':
            rows=atoi(dtpref_rows)+5
            cols=atoi(dtpref_cols)+5
	    e='Friday, 31-Dec-99 23:59:59 GMT'
	    resp=REQUEST['RESPONSE']
	    resp.setCookie('dtpref_rows',str(rows),path='/',expires=e)
	    resp.setCookie('dtpref_cols',str(cols),path='/',expires=e)
	    return self.manage_main(self,REQUEST,title=title,__str__=data,
				    dtpref_cols=cols,dtpref_rows=rows)
	self.title=title
	self.munge(data)
	if REQUEST: return MessageDialog(
		    title  ='Success!',
		    message='Your changes have been saved',
		    action ='manage_main')

    def manage_upload(self,file='', REQUEST=None):
	""" """
	self._validateProxy(REQUEST)
	self.munge(file.read())
	if REQUEST: return MessageDialog(
		    title  ='Success!',
		    message='Your changes have been saved',
		    action ='manage_main')

    PUT__roles__='Manager',
    def PUT(self, BODY, REQUEST):
	""" """
	self._validateProxy(REQUEST)
	self.munge(BODY)
	return 'OK'

    def manage_haveProxy(self,r): return r in self._proxy_roles

    def _validateProxy(self, request, roles=None):
	if roles is None: roles=self._proxy_roles
	if not roles: return
	user=u=request.get('AUTHENTICATED_USER',None)
	if user is not None:
	    user=user.hasRole
	    for r in roles:
		if r and not user(None, (r,)):
		    user=None
		    break

	    if user is not None: return

	raise 'Forbidden', (
	    'You are not authorized to change <em>%s</em> because you '
	    'do not have proxy roles.\n<!--%s, %s-->' % (self.__name__, u, roles))
	    

    def manage_proxy(self, roles=(), REQUEST=None):
	"Change Proxy Roles"
	self._validateProxy(REQUEST, roles)
	self._validateProxy(REQUEST)
	self._proxy_roles=tuple(roles)
	if REQUEST: return MessageDialog(
		    title  ='Success!',
		    message='Your changes have been saved',
		    action ='manage_main')

default_html="""<!--#var standard_html_header-->
<H2><!--#var title_or_id--> <!--#var document_title--></H2>
<P>This is the <!--#var document_id--> Document in 
the <!--#var title_and_id--> Folder.</P>
<!--#var standard_html_footer-->"""

manage_addDocumentForm=HTMLFile('documentAdd', globals())

def manage_addDocument(self,id,title='',file='',REQUEST=None):
    """ """
    if not file: file=default_html
    i=Document(file, __name__=id)
    i.title=title
    self._setObject(id,i)
    if REQUEST is not None: return self.manage_main(self,REQUEST)
    return ''

class DocumentHandler:
    """ """

    def documentIds(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Document':
		t.append(i['id'])
	return t

    def documentValues(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Document':
		t.append(getattr(self,i['id']))
	return t

def decapitate(html, RESPONSE=None,
	       header_re=regex.compile(
		   '\(\('
		   	  '[^\0- <>:]+:[^\n]*\n'
		      '\|'
		   	  '[ \t]+[^\0- ][^\n]*\n'
		   '\)+\)[ \t]*\n\([\0-\377]+\)'
		   ),
	       space_re=regex.compile('\([ \t]+\)'),
	       name_re=regex.compile('\([^\0- <>:]+\):\([^\n]*\)'),
	       ):
    if header_re.match(html) < 0: return html

    headers, html = header_re.group(1,3)

    headers=split(headers,'\n')

    i=1
    while i < len(headers):
	if not headers[i]:
	    del headers[i]
	elif space_re.match(headers[i]) >= 0:
	    headers[i-1]="%s %s" % (headers[i-1],
				    headers[i][len(space_re.group(1)):])
	    del headers[i]
	else:
	    i=i+1

    for i in range(len(headers)):
	if name_re.match(headers[i]) >= 0:
	    k, v = name_re.group(1,2)
	    v=strip(v)
	else:
	    raise ValueError, 'Invalid Header (%d): %s ' % (i,headers[i])
	RESPONSE.setHeader(k,v)

    return html

