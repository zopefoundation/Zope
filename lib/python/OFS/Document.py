"""Document object"""

__version__='$Revision: 1.8 $'[11:-2]

from STPDocumentTemplate import HTML
from Globals import HTMLFile
from string import join, split, strip, rfind
import AccessControl.ACL
import regex

class Document(HTML, AccessControl.ACL.RoleManager):
    """A Document object"""
    meta_type  ='Document'
    title=''
    icon       ='OFS/Document_icon.gif'

    __state_names__=HTML.__state_names__+('title','__roles__')

    def document_template_form_header(self):
	try: roles=join(self.__roles__)
	except: roles=''
	return ("""<table>
	           <tr><th>Title:</th><td>
                   <input type=text name=title SIZE="50" value="%s"></td></tr>
		   <tr><th>Roles:</th><td>
                   <input type=text name=roles SIZE="50" value="%s"></td></tr>
                   </table>""" % (self.title, roles))


    def initvars(self, mapping, vars):
	"""Hook to override signature so we can detect whether we are
	running from the web"""
	HTML.initvars(self, mapping, vars)
	self.func_code.__init__(('self','REQUEST','RESPONSE'))
	self.func_defaults=(None,)

    def __call__(self, client=None, REQUEST={}, RESPONSE=None, **kw):
	r=apply(HTML.__call__, (self, client, REQUEST), kw)
	if RESPONSE is None: return r
	return decapitate(r, RESPONSE)

    def manage_edit(self,data,title,roles,REQUEST=None):
	"""Edit method"""
	self.title=title
	self.parse_roles_string(roles)
	REQUEST['CANCEL_ACTION']="%s/manage_main" % REQUEST['URL2']
	return HTML.manage_edit(self,data,REQUEST)



default_html="""<!--#var standard_html_header-->
New Document
<!--#var standard_html_footer-->"""


class DocumentHandler:
    """Document object handler mixin"""
    meta_types=({'name':'Document', 'action':'manage_addDocumentForm'},)

    manage_addDocumentForm=HTMLFile('OFS/documentAdd')

    def manage_addDocument(self,id,title,roles,REQUEST,file=''):
	"""Add a new Document object"""
	if not file: file=default_html
        i=Document(file, __name__=id)
	i.title=title
	i.parse_roles_string(roles)
	self._setObject(id,i)
	if REQUEST: return self.manage_main(self,REQUEST)

    def documentIds(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Document': t.append(i['id'])
	return t

    def documentValues(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Document': t.append(getattr(self,i['id']))
	return t

    def documentItems(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Document':
		n=i['id']
		t.append((n,getattr(self,n)))
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

