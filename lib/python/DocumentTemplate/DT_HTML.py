
"""HTML formated DocumentTemplates

$Id: DT_HTML.py,v 1.6 1998/04/02 17:37:35 jim Exp $"""

from DT_String import String, FileMixin
import DT_Doc, DT_String, regex
from DT_Util import *
from regsub import gsub
from string import strip, find

class dtml_re_class:

    def search(self, text, start=0,
	       name_match=regex.compile('[\0- ]*[a-zA-Z]+[\0- ]*').match,
	       end_match=regex.compile('[\0- ]*\(/\|end\)',
				       regex.casefold).match,
	       ):
	s=find(text,'<!--#',start)
	if s < 0: return s
	e=find(text,'-->',s)
	if e < 0: return e

	n=s+5
	l=end_match(text,n)
	if l > 0:
	    end=strip(text[n:n+l])
	    n=n+l
	else: end=''

	l=name_match(text,n)
	if l < 0: return l
	a=n+l
	name=strip(text[n:a])

	args=strip(text[a:e])

	d=self.__dict__
	d[0]=text[s:e+3]
	d[1]=end
	d['end']= end
	d[2]=name
	d['name']=name
	d[3]=args
	d['args']=args

	return s

    def group(self,*args):
	g=self.__dict__
	if len(args)==1: return g[args[0]]
	r=[]
	for arg in args:
	    r.append(g[arg])
	return tuple(r)
	

class HTML(DT_String.String):
    __doc__=DT_Doc.HTML__doc__

    def tagre(self):
	return dtml_re_class()

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
		raise ParseError, ('unexpected end tag', tag)
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
		   text=None,
		   character_entities=(
		       (regex.compile('&'), '&amp;'),
		       (regex.compile("<"), '&lt;' ),
		       (regex.compile(">"), '&gt;' ),
		       (regex.compile('"'), '&quot;'))): #"
        if text is None: text=self.read_raw()
	for re,name in character_entities:
	    text=gsub(re,name,text)
	return text

    errQuote=quotedHTML

    def __str__(self):
	return self.quotedHTML()

    def management_interface(self):
	'''Hook to allow public execution of management interface with
	everything else private.'''
	return self

    def manage_editForm(self, PARENT_URL, REQUEST):
	'''Display doc template editing form''' #"
	
	return self._manage_editForm(
	    self,
	    mapping=REQUEST,
	    __str__=str(self),
	    PARENT_URL=PARENT_URL
	    )

    manage_editDocument=manage=manage_editForm

class HTMLDefault(HTML):
    '''\
    HTML document templates that edit themselves through copy.

    This is to make a distinction from HTML objects that should edit
    themselves in place.
    '''
    copy_class=HTML

    def manage_edit(self,data,PARENTS,URL1,REQUEST):
	'edit a template'
	newHTML=self.copy_class(data,self.globals,self.__name__)
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
	'''Display doc template editing form'''

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
# Revision 1.6  1998/04/02 17:37:35  jim
# Major redesign of block rendering. The code inside a block tag is
# compiled as a template but only the templates blocks are saved, and
# later rendered directly with render_blocks.
#
# Added with tag.
#
# Also, for the HTML syntax, we now allow spaces after # and after end
# or '/'.  So, the tags::
#
#   <!--#
#     with spam
#     -->
#
# and::
#
#   <!--#
#     end with
#     -->
#
# are valid.
#
# Revision 1.5  1997/10/27 17:35:32  jim
# Removed old validation machinery.
#
# Added a regex-like parser that doesn't have regex's tendency to hang
# the process.  Maybe I'll be able to use re in the future. ;-)
#
# Added errQuote to aid in parse error message generation.
#
# Revision 1.4  1997/09/25 18:56:37  jim
# fixed problem in reporting errors
#
# Revision 1.3  1997/09/22 14:42:08  jim
# *** empty log message ***
#
# Revision 1.2  1997/09/02 19:04:09  jim
# Got rid of ^Ms
#
# Revision 1.1  1997/08/27 18:55:41  jim
# initial
#
