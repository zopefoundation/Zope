"""Document object"""

__version__='$Revision: 1.57 $'[11:-2]

from Globals import HTML, HTMLFile, MessageDialog
from string import join,split,strip,rfind,atoi,lower
from AccessControl.Role import RoleManager
from SimpleItem import Item_w__name__
from Acquisition import Explicit
import regex, Globals, sys
import cDocumentTemplate

class Document(cDocumentTemplate.cDocument, HTML, Explicit,
	       RoleManager, Item_w__name__,
	       ):
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
    ('Change Documents', ['manage_edit','manage_upload','PUT']),
    ('Change proxy roles', ['manage_proxyForm','manage_proxy']),
    ('View', ['__call__', '']),
    )

    _state_name={'raw':1, 'globals':1, '__name__':1, '_vars':1,
		 '_proxy_roles':1}.has_key

    def __getstate__(self):
	r={}
        state_name=self._state_name
        for k, v in self.__dict__.items():
            if state_name(k) or k[-11:]=='_Permission' or k[-9:]=="__roles__":
                r[k]=v

	return r
   

    def __call__(self, client=None, REQUEST={}, RESPONSE=None, **kw):
	""" """
	kw['document_id']   =self.id
        kw['document_title']=self.title
	try:
	    try: r=apply(HTML.__call__, (self, client, REQUEST), kw)
	    except:
		if self.id()=='standard_error_message':
		    raise sys.exc_type, sys.exc_value, sys.exc_traceback
		error_type=sys.exc_type
		error_value=sys.exc_value
		tb=sys.exc_traceback
		if lower(error_type) in ('redirect',):
		    raise error_type, error_value, tb
		if (type(error_value) is type('') and
		    regex.search('[a-zA-Z]>', error_value) > 0):
		    error_message=error_value
		else:
		    error_message=''
		error_tb=pretty_tb(error_type, error_value, tb)
		if client is not None: c=client
		else: c=self.aq_parent
		try:
		    s=getattr(c, 'standard_error_message')
		    v=HTML.__call__(s, c, REQUEST, error_type=error_type,
				    error_value=error_value,
				    error_tb=error_tb, error_traceback=error_tb,
				    error_message=error_message)
		except:
		    v='Sorry, an error occured'
		raise error_type, v, tb
	finally: tb=None
		
	if RESPONSE is None: return r
	return decapitate(r, RESPONSE)

    def oldvalidate(self, inst, parent, name, value, md):
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


	if inst is parent:
	    raise 'Unauthorized', (
		'You are not authorized to access <em>%s</em>.' % name)

	return 0

    manage_editForm=HTMLFile('documentEdit', globals())
    manage_uploadForm=HTMLFile('documentUpload', globals())
    manage=manage_main=manage_editDocument=manage_editForm
    manage_proxyForm=HTMLFile('documentProxy', globals())


    _size_changes={
        'Bigger': (5,5),
        'Smaller': (-5,-5),
        'Narrower': (0,-5),
        'Wider': (0,5),
        'Taller': (5,0),
        'Shorter': (-5,0),
        }

    def _er(self,data,title,SUBMIT,dtpref_cols,dtpref_rows,REQUEST):
        dr,dc = self._size_changes[SUBMIT]
        
        rows=max(1,atoi(dtpref_rows)+dr)
        cols=max(40,atoi(dtpref_cols)+dc)
        e='Friday, 31-Dec-99 23:59:59 GMT'
        resp=REQUEST['RESPONSE']
        resp.setCookie('dtpref_rows',str(rows),path='/',expires=e)
        resp.setCookie('dtpref_cols',str(cols),path='/',expires=e)
        return self.manage_main(
	    self,REQUEST,title=title,__str__=self.quotedHTML(data),
	    dtpref_cols=cols,dtpref_rows=rows)

    def manage_edit(self,data,title,SUBMIT='Change',dtpref_cols='50',
		    dtpref_rows='20',REQUEST=None):
	"""
	Replaces a Documents contents with Data, Title with Title.

	The SUBMIT parameter is also used to change the size of the editing
	area on the default Document edit screen.  If the value is "Smaller",
	the rows and columns decrease by 5.  If the value is "Bigger", the
	rows and columns increase by 5.  If any other or no value is supplied,
	the data gets checked for DTML errors and is saved.
	"""
	self._validateProxy(REQUEST)
        if self._size_changes.has_key(SUBMIT):
            return self._er(data,title,SUBMIT,dtpref_cols,dtpref_rows,REQUEST)

	self.title=title
	self.munge(data)
	if REQUEST: return MessageDialog(
		    title  ='Success!',
		    message='Your changes have been saved',
		    action ='manage_main')

    def manage_upload(self,file='', REQUEST=None):
	"""
	replace the contents of the document with the text in file.
	"""
	self._validateProxy(REQUEST)
	self.munge(file.read())
	if REQUEST: return MessageDialog(
		    title  ='Success!',
		    message='Your changes have been saved',
		    action ='manage_main')

    def PUT(self, BODY, REQUEST):
	"""
   replaces the contents of the document with the BODY of an HTTP PUT request.
	"""
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
    """
    Add a Document object with the contents of file.

    If 'file' is empty or unspecified, the created documents contents are set
    to Principia's preset default.
    """
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

def format_exception(etype,value,tb,limit=None):
    import traceback
    result=['Traceback (innermost last):']
    if limit is None:
	    if hasattr(sys, 'tracebacklimit'):
		    limit = sys.tracebacklimit
    n = 0
    while tb is not None and (limit is None or n < limit):
	    f = tb.tb_frame
	    lineno = tb.tb_lineno
	    co = f.f_code
	    filename = co.co_filename
	    name = co.co_name
	    locals=f.f_locals
	    result.append('  File %s, line %d, in %s'
			  % (filename,lineno,name))
	    try: result.append('    (Object: %s)' %
			       locals[co.co_varnames[0]].__name__)
	    except: pass
	    try: result.append('    (Info: %s)' %
			       str(locals['__traceback_info__']))
	    except: pass
	    tb = tb.tb_next
	    n = n+1
    result.append(join(traceback.format_exception_only(etype, value),
		       ' '))
#    sys.exc_type,sys.exc_value,sys.exc_traceback=etype,value,tb
    return result

def pretty_tb(t,v,tb):
    tb=format_exception(t,v,tb,200)
    tb=join(tb,'\n')
    return tb

