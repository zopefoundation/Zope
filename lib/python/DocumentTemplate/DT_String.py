
from string import *
import DT_Doc, DT_Var, DT_In, DT_If, regex, ts_regex, DT_Raise, DT_With
Var=DT_Var.Var

from DT_Util import *
from DT_Comment import Comment

class String:
    __doc__=DT_Doc.String__doc__
    isDocTemp=1

    # Document Templates masquerade as functions:
    class func_code: pass
    func_code=func_code()
    func_code.co_varnames='self','REQUEST'
    func_code.co_argcount=2
    func_defaults=()

    def errQuote(self, s): return s
      
    def parse_error(self, mess, tag, text, start):
	raise ParseError, "%s, for tag %s, on line %s of %s<p>" % (
	    mess, self.errQuote(tag), len(split(text[:start],'\n')),
	    self.errQuote(self.__name__))

    commands={
	'var': DT_Var.Var,
	'call': DT_Var.Call,
	'in': DT_In.In,
	'with': DT_With.With,
	'if': DT_If.If,
	'unless': DT_If.Unless,
	'else': DT_If.Else,
	'comment': Comment,
	'raise': DT_Raise.Raise,
	}

    def SubTemplate(self, name): return String('', __name__=name)

    def tagre(self):
	return ts_regex.symcomp(
	    '%('                                     # beginning
	    '\(<name>[a-zA-Z0-9_/.-]+\)'                       # tag name
	    '\('
	    '[\0- ]+'                                # space after tag name
	    '\(<args>\([^)"]+\("[^"]*"\)?\)*\)'      # arguments
	    '\)?'
	    ')\(<fmt>[0-9]*[.]?[0-9]*[a-z]\|[]![]\)' # end
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
	tag, name, args, fmt =tagre.group(0, 'name', 'args', 'fmt')
	args=args and strip(args) or ''

	if fmt==']':
	    if not command or name != command.name:
		raise ParseError, ('unexpected end tag', tag)
	    return tag, args, None, None
	elif fmt=='[' or fmt=='!':
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
        else:
	    # Var command
	    args=args and ("%s %s" % (name, args)) or name
	    return tag, args, Var, None

    def varExtra(self,tagre): return tagre.group('fmt')

    def parse(self,text,start=0,result=None,tagre=None):
	if result is None: result=[]
	if tagre is None: tagre=self.tagre()
        l=tagre.search(text,start)
	while l >= 0:

	    try: tag, args, command, coname = self.parseTag(tagre)
	    except ParseError, m: self.parse_error(m[0],m[1],text,l)

	    s=text[start:l]
	    if s: result.append(s)
	    start=l+len(tag)

	    if hasattr(command,'blockContinuations'):
		start=self.parse_block(text, start, result, tagre,
				       tag, l, args, command)
	    else:
		try:
		    if command is Var: r=command(args, self.varExtra(tagre))
		    else: r=command(args)
		    if hasattr(r,'simple_form'): r=r.simple_form
		    result.append(r)
		except ParseError, m: self.parse_error(m[0],tag,text,l)

	    l=tagre.search(text,start)

	text=text[start:]
	if text: result.append(text)
	return result

    def skip_eol(self, text, start, eol=regex.compile('[ \t]*\n')):
        # if block open is followed by newline, then skip past newline
	l=eol.match(text,start)
	if l > 0: start=start+l
	return start

    def parse_block(self, text, start, result, tagre,
		    stag, sloc, sargs, scommand):

        start=self.skip_eol(text,start)

        blocks=[]
        tname=scommand.name
	sname=stag
	sstart=start
	sa=sargs
        while 1:

	    l=tagre.search(text,start)
	    if l < 0: self.parse_error('No closing tag', stag, text, sloc)

	    try: tag, args, command, coname= self.parseTag(tagre,scommand,sa)
	    except ParseError, m: self.parse_error(m[0],m[1], text, l)
	    
	    if command:
		start=l+len(tag)
		if hasattr(command, 'blockContinuations'):
		    # New open tag.  Need to find closing tag.
		    start=self.parse_close(text, start, tagre, tag, l,
					   command, args)
	    else:
		# Either a continuation tag or an end tag
		section=self.SubTemplate(sname)
		section.blocks=self.parse(text[:l],sstart)
		section.cooked=None
		blocks.append((tname,sargs,section))
    
		start=self.skip_eol(text,l+len(tag))

		if coname:
		    tname=coname
		    sname=tag
		    sargs=args
		    sstart=start
		else:
		    try:
			r=scommand(blocks)
			if hasattr(r,'simple_form'): r=r.simple_form
			result.append(r)
		    except ParseError, m: self.parse_error(m[0],stag,text,l)

		    return start
    
    def parse_close(self, text, start, tagre, stag, sloc, scommand, sa):
        while 1:
	    l=tagre.search(text,start)
	    if l < 0: self.parse_error('No closing tag', stag, text, sloc)

	    try: tag, args, command, coname= self.parseTag(tagre,scommand,sa)
	    except ParseError, m: self.parse_error(m[0],m[1], text, l)

	    start=l+len(tag)
	    if command:
		if hasattr(command, 'blockContinuations'):
		    # New open tag.  Need to find closing tag.
		    start=self.parse_close(text, start, tagre, tag, l,
					   command,args)
	    elif not coname: return start

    shared_globals={}

    def __init__(self, source_string='', mapping=None, __name__='<string>',
		 **vars):
	"""\
	Create a document template from a string.

	The optional parameter, 'mapping', may be used to provide a
	mapping object containing defaults for values to be inserted.
	"""
       	self.raw=source_string
	self.initvars(mapping, vars)
	self.setName(__name__)

    def name(self): return self.__name__
    id=name

    def setName(self,v): self.__dict__['__name__']=v

    def default(self,name=None,**kw):
	"""\
	Change or query default values in a document template.

	If a name is specified, the value of the named default value
	before the operation is returned.

	Keyword arguments are used to provide default values.
	"""
	if name: name=self.globals[name]
	for key in kw.keys(): self.globals[key]=kw[key]
	return name

    def var(self,name=None,**kw):
	"""\
	Change or query a variable in a document template.

	If a name is specified, the value of the named variable before
	the operation is returned.

	Keyword arguments are used to provide variable values.
	"""
	if name: name=self._vars[name]
	for key in kw.keys(): self._vars[key]=kw[key]
	return name

    def munge(self,source_string=None,mapping=None,**vars):
	"""\
	Change the text or default values for a document template.
	"""
	if mapping is not None or vars:
	    self.initvars(mapping, vars)
	if source_string is not None: 
	    self.raw=source_string
	self.cooked=self.cook()

    def manage_edit(self,data,REQUEST=None):
	self.munge(data)

    def read_raw(self,raw=None):
	return self.raw

    def read(self,raw=None):
	return self.read_raw()

    def cook(self):
	self.blocks=self.parse(self.read())

    def initvars(self, globals, vars):
	if globals:
	    for k in globals.keys():
		if k[:1] != '_' and not vars.has_key(k): vars[k]=globals[k]
	self.globals=vars
	self._vars={}

    __state_names__=('raw', 'globals', '__name__', '_vars')

    def __getstate__(self):
	r={}
	for k in self.__state_names__:
	    try: r[k]=getattr(self,k)
	    except: pass
	return r

    def __setstate__(self,s,hack=('',{},'<string>',{},'')):
	try:
	    for k in s.keys(): self.__dict__[k]=s[k]
	except: 
	    self.raw,self.globals,self.__dict__['name'],self._vars,dummy=(
		s+hack[len(s)-len(hack):])

    def __call__(self,client=None,mapping={},**kw):
	'''\
	Generate a document from a document template.

	The document will be generated by inserting values into the
	format string specified when the document template was
	created.  Values are inserted using standard python named
	string formats.

	The optional argument 'client' is used to specify a object
	containing values to be looked up.  Values will be looked up
	using getattr, so inheritence of values is supported.  Note
	that names beginning with '_' will not be looked up from the
	client. 

	The optional argument, 'mapping' is used to specify a mapping
	object containing values to be inserted.

	Values to be inserted may also be specified using keyword
	arguments. 

	Values will be inserted from one of several sources.  The
	sources, in the order in which they are consulted, are:

	  o  Keyword arguments,

	  o  The 'client' argument,

	  o  The 'mapping' argument,

	  o  The keyword arguments provided when the object was
	     created, and

	  o  The 'mapping' argument provided when the template was
	     created. 

	'''
	# print '============================================================'
	# print '__called__'
	# print self.raw
	# print kw
	# print client
	# print mapping
	# print '============================================================'

	if mapping is None: mapping = {}

	if not hasattr(self,'cooked'):
	    try: changed=self.__changed__()
	    except: changed=1
	    cooked=self.cook()
	    self.cooked=cooked
	    if not changed: self.__changed__(0)

	pushed=None
	try:
	    if mapping.__class__ is TemplateDict: pushed=0
	except: pass

	globals=self.globals
	if pushed is not None:
	    # We were passed a TemplateDict, so we must be a sub-template
	    md=mapping
	    push=md._push
	    if globals:
		push(self.globals)
		pushed=pushed+1
	else:
	    md=TemplateDict()
	    push=md._push
	    shared_globals=self.shared_globals
	    if shared_globals: push(shared_globals)
	    if globals: push(globals)
	    if mapping:
		push(mapping)
		if hasattr(mapping,'AUTHENTICATED_USER'):
		    md.AUTHENTICATED_USER=mapping['AUTHENTICATED_USER']
	    md.validate=self.validate
	    if client is not None: md.this=client
	    pushed=0

	level=md.level
	if level > 200: raise SystemError, (
	    'infinite recursion in document template')
	md.level=level+1

	if client is not None:
	    push(InstanceDict(client,md)) # Circ. Ref. 8-|
	    pushed=pushed+1

	if self._vars: 
	    push(self._vars)
	    pushed=pushed+1

	if kw:
	    push(kw)
	    pushed=pushed+1

	try:
	    return render_blocks(self.blocks,md)
	finally:
	    if pushed: md._pop(pushed) # Get rid of circular reference!
	    md.level=level # Restore previous level

    validate=None

    def __str__(self):
	return self.read()

class FileMixin:
    # Mix-in class to abstract certain file-related attributes
    edited_source=''
    __state_names__=(
	String.__state_names__ +
	('edited_source',))
    
    def __init__(self, file_name='', mapping=None, **vars):
	"""\
	Create a document template based on a named file.

	The optional parameter, 'mapping', may be used to provide a
	mapping object containing defaults for values to be inserted.
	"""
       	self.raw=file_name
	self.initvars(mapping, vars)
	self.setName(file_name)

    def read_raw(self):
	if self.edited_source: return self.edited_source
	if self.raw: return open(self.raw,'r').read()
	return ''

class File(FileMixin, String):
    """\
    Document templates read from files.

    If the object is pickled, the file name, rather
    than the file contents is pickled.  When the object is
    unpickled, then the file will be re-read to obtain the string.
    Note that the file will not be read until the document
    template is used the first time.
    """
    def manage_edit(self,data): raise TypeError, 'cannot edit files'

