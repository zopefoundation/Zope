"""Document object"""

__version__='$Revision: 1.5 $'[11:-2]

from STPDocumentTemplate import HTML
from Globals import shared_dt_globals,HTMLFile
from string import join, split, strip
import AccessControl.ACL

class Document(HTML, AccessControl.ACL.RoleManager):
    """A Document object"""
    meta_type  ='Document'
    title=''
    icon       ='OFS/Document_icon.gif'

    __state_names__=HTML.__state_names__+('title','__roles__')
    shared_globals =shared_dt_globals
    manage_edit__allow_groups__    ={None:None}

    def document_template_form_header(self):
	try: roles=join(self.__roles__)
	except: roles=''
	return ("""<br>Title: 
                   <input type=text name=title SIZE="50" value="%s">
		   <br>Roles:
                   <input type=text name=roles SIZE="50" value="%s">
                   <P>""" % (self.title, roles))

    def manage_edit(self,data,title,roles,REQUEST=None):
	"""Edit method"""
	self.title=title
	self.parse_roles_string(roles)
	return HTML.manage_edit(self,data,REQUEST)



default_html="""
<HTML>
<HEAD>
<TITLE>New Document</TITLE>
</HEAD>
<BODY>
New Document
</BODY>
</HTML>"""


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
	return self.manage_main(self,REQUEST)

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
