"""Document object"""

__version__='$Revision: 1.1 $'[11:-2]

from STPDocumentTemplate import HTML
from Globals import shared_dt_globals,HTMLFile

class Document(HTML):
    """A Document object"""
    meta_type  ='Document'
    description=''
    icon       ='OFS/document.jpg'

    __state_names__=HTML.__state_names__+('description',)
    shared_globals =shared_dt_globals
    manage_edit__allow_groups__    =None
    manage_editForm__allow_groups__=None

    def document_template_form_header(self):
	return ("""<br>Description: 
                   <input type=text name=description SIZE="50" value="%s">
                   <P>""" % self.description)

    def manage_edit(self,data,description,REQUEST=None):
	"""Edit method"""
	self.description=description
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

    def manage_addDocument(self,name,description,REQUEST,file=''):
	"""Add a new Document object"""
	if not file: file=default_html
        i=Document(file, __name__=name)
	i.description=description
	self._setObject(name,i)
	return self.manage_main(self,REQUEST)

    def documentNames(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Document': t.append(i['name'])
	return t

    def documentValues(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Document': t.append(getattr(self,i['name']))
	return t

    def documentItems(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Document':
		n=i['name']
		t.append((n,getattr(self,n)))
	return t
