
"""HTML formated DocumentTemplates

$Id: DT_HTML.py,v 1.2 1997/09/02 19:04:09 jim Exp $"""

from DT_String import String, FileMixin
import DT_Doc, DT_String, regex
from regsub import gsub
from string import strip

class HTML(DT_String.String):
    __doc__=DT_Doc.HTML__doc__

    def tagre(self):
	return regex.symcomp(
	    '<!--#'                                 # beginning
	    '\(<end>/\|end\)?'                      # end tag marker
	    '\(<name>[a-z]+\)'                      # tag name
	    '[\0- ]*'                               # space after tag name
	    '\(<args>\([^>"]+\("[^"]*"\)?\)*\)'     # arguments
	    '-->'                                   # end
	    , regex.casefold) 

    def parseTag(self, tagre, command=None, sargs=''):
	"""Parse a tag using an already matched re

	Return: tag, args, command, coname

	where: tag is the tag,
               args is the tag\'s argument string,
	       command is a corresponding command info structure if the
                  tag is a start tag, or None otherwise, and
	       coname is the name of a continue tag (e.g. else)
	         or None otherwise
	"""
	tag, end, name, args, =tagre.group(0, 'end', 'name', 'args')
	args=strip(args)
	if end:
	    if not command or name != command.name:
		raise ParseError, 'unexpected end tag'
	    return tag, args, None, None

	if command and name in command.blockContinuations:

	    if name=='else' and args:
		# Waaaaaah! Have to special case else because of
		# old else start tag usage. Waaaaaaah!
		l=len(args)
		if not (args==sargs or
			args==sargs[:l] and sargs[l:l+1] in ' \t\n'):
		    return tag, args, self.commands[name], None
	    
	    return tag, args, None, name

	try: return tag, args, self.commands[name], None
	except KeyError:
	    raise ParseError, ('Unexpected tag', tag)

    def SubTemplate(self, name): return HTML('', __name__=name)

    def varExtra(self,tagre): return 's'

    def manage_edit(self,data,REQUEST=None):
	'edit a template'
	self.munge(data)
	if REQUEST: return self.editConfirmation(self,REQUEST)

    def quotedHTML(self,
		   character_entities=(
		       (regex.compile('&'), '&amp;'),
		       (regex.compile("<"), '&lt;' ),
		       (regex.compile(">"), '&gt;' ),
		       (regex.compile('"'), '&quot;'))): #"
        text=self.read_raw()
	for re,name in character_entities:
	    text=gsub(re,name,text)
	return text

    def __str__(self):
	return self.quotedHTML()

    def management_interface(self):
	'''Hook to allow public execution of management interface with
	everything else private.'''
	return self

    def manage_editForm(self, PARENT_URL, REQUEST):
	'''Display doc template editing form''' #"
	
	self._manage_editForm.validator(self.validate)
	return self._manage_editForm(
	    self,
	    mapping=REQUEST,
	    __str__=str(self),
	    vars=self._names.items(),
	    PARENT_URL=PARENT_URL
	    )

    manage_editDocument=manage=manage_editForm

    def validate(self, key, value=None):
	if os.environ.has_key(key): return 1
	return 0

class HTMLDefault(HTML):
    '''\
    HTML document templates that edit themselves through copy.

    This is to make a distinction from HTML objects that should edit
    themselves in place.
    '''
    copy_class=HTML

    def manage_edit(self,data,PARENTS,URL1,REQUEST):
	'edit a template'
	newHTML=self.copy_class(data,self.globals,self.__name__,
				self._names, self._validator)
	setattr(PARENTS[1],URL1[rfind(URL1,'/')+1:],newHTML)
	return self.editConfirmation(self,REQUEST)


class HTMLFile(FileMixin, HTML):
    """\
    HTML Document templates read from files.

    If the object is pickled, the file name, rather
    than the file contents is pickled.  When the object is
    unpickled, then the file will be re-read to obtain the string.
    Note that the file will not be read until the document
    template is used the first time.
    """

    def manage_default(self, REQUEST=None):
	'Revert to factory defaults'
	if self.edited_source:
	    self.edited_source=''
	    self.cooked=self.cook()
	if REQUEST: return self.editConfirmation(self,REQUEST)

    def manage_editForm(self, PARENT_URL, REQUEST):
	'''Display doc template editing form''' #"

	self._manage_editForm.validator(self.validate)
	return self._manage_editForm(mapping=REQUEST,
				     document_template_edit_width=
				     self.document_template_edit_width,
				     document_template_edit_header=
				     self.document_template_edit_header,
				     document_template_form_header=
				     self.document_template_form_header,
				     document_template_edit_footer=
				     self.document_template_edit_footer,
				     PARENT_URL=PARENT_URL,
				     __str__=str(self),
				     vars=self._names.items(),
				     FactoryDefaultString=FactoryDefaultString,
				     )
    manage_editDocument=manage=manage_editForm

    def manage_edit(self,data,
		    PARENTS=[],URL1='',URL2='',REQUEST='', SUBMIT='',
		    crlf=regex.compile('\r\n\|\n\r')):
	'edit a template'
	if SUBMIT==FactoryDefaultString: return self.manage_default(REQUEST)
	data=gsub(crlf,'\n',data)
	if self.edited_source:
	    self.edited_source=data
	    self.cooked=self.cook()
	else:
	    __traceback_info__=self.__class__
	    newHTML=self.__class__()
	    newHTML.__setstate__(self.__getstate__())
	    newHTML.edited_source=data
	    setattr(PARENTS[1],URL1[rfind(URL1,'/')+1:],newHTML)
	if REQUEST: return self.editConfirmation(self,REQUEST)

##########################################################################
#
# $Log: DT_HTML.py,v $
# Revision 1.2  1997/09/02 19:04:09  jim
# Got rid of ^Ms
#
# Revision 1.1  1997/08/27 18:55:41  jim
# initial
#
