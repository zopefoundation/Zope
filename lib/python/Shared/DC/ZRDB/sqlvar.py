#!/usr/local/bin/python 
# $What$

'''Inserting values with the 'sqlvar' tag

    The 'sqlvar' tag is used to type-safely insert values into SQL
    text.  The 'sqlvar' tag is similar to the 'var' tag, except that
    it replaces text formatting parameters with SQL type information.

    The sqlvar tag has the following attributes:

      name -- The name of the variable to insert. As with other
              DTML tags, the 'name=' prefix may be, and usually is,
              ommitted.

      type -- The data type of the value to be inserted.  This
	      attribute is required and may be one of 'string',
	      'int', 'float', or 'nb'.  The 'nb' data type indicates a
	      string that must have a length that is greater than 0.

      optional -- A flag indicating that a value is optional.  If a
		  value is optional and is not provided (or is blank
		  when a non-blank value is expected), then the string
		  'null' is inserted.

    For example, given the tag::

      <!--#sqlvar x type=nb optional>

    if the value of 'x' is::
 
      Let\'s do it

    then the text inserted is:

      'Let''s do it'

    however, if x is ommitted or an empty string, then the value
    inserted is 'null'.
'''
__rcs_id__='$Id: sqlvar.py,v 1.1 1998/03/17 19:31:22 jim Exp $'

############################################################################
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################ 
__version__='$Revision: 1.1 $'[11:-2]

from DocumentTemplate.DT_Util import *
from string import find, split, join, atoi, atof
StringType=type('')

class SQLVar: 
    name='sqlvar'

    def __init__(self, args):
	args = parse_params(args, name='', type=None, optional=1)
	self.__name__ = name_param(args,'sqlvar')
	self.args=args
	if not args.has_key('type'):
	    raise ParseError, ('the type attribute is required', 'dtvar')
	t=args['type']
	if not valid_type(t):
	    raise ParseError, ('invalid type, %s' % t, 'dtvar')

    def render(self, md):
	name=self.__name__
	args=self.args
	t=args['type']
	try: v = md[name]
	except:
	    if args.has_key('optional') and args['optional']: return 'null'
	    raise 'Missing Input', 'Missing input variable, <em>%s</em>' % name
	if t=='int':
	    try:
		if type(v) is StringType: atoi(v)
		else: v=str(int(v))
	    except:
		if not v and args.has_key('optional') and args['optional']:
		    return 'null'
		raise ValueError, (
		    'Invalid integer value for <em>%s</em>' % name)
	elif t=='float':
	    try:
		if type(v) is StringType: atof(v)
		else: v=str(float(v))
	    except:
		if not v and args.has_key('optional') and args['optional']:
		    return 'null'
		raise ValueError, (
		    'Invalid floating-point value for <em>%s</em>' % name)
	else:
	    v=str(v)
	    if not v and t=='nb':
		raise ValueError, (
		    'Invalid empty string value for <em>%s</em>' % name)
	    if find(v,"\'") >= 0: v=join(split(v,"\'"),"''")
	    v="'%s'" % v

	return v

    __call__=render

valid_type={'int':1, 'float':1, 'string':1, 'nb': 1}.has_key

############################################################################
# $Log: sqlvar.py,v $
# Revision 1.1  1998/03/17 19:31:22  jim
# added new sql tags
#
# Revision 1.9  1998/01/12 16:47:34  jim
# Changed a number of custom formats to modifiers, since they can
# be applies cumulatively.
# Updated documentation.
#
# Revision 1.8  1998/01/08 20:57:34  jim
# *** empty log message ***
#
# Revision 1.7  1998/01/05 21:23:01  jim
# Added support for fmt="" to allow vars with side effects.
#
# Revision 1.6  1997/12/12 16:19:06  jim
# Added additional special formats, structured-text and sql-quote.
# Also changed the way formats are handled.  This has (and will)
# reveal now hidden fmt=invalid-thing errors.
#
# Revision 1.5  1997/10/27 17:39:27  jim
# removed a comment burp.
#
# Revision 1.4  1997/10/23 14:27:47  jim
# Added truncation support via size and etc attributes.
#
# Revision 1.3  1997/10/23 13:30:16  jim
# Added comma-numeric format.
#
# Revision 1.2  1997/09/22 14:42:51  jim
# added expr
#
# Revision 1.1  1997/08/27 18:55:44  jim
# initial
#
#
