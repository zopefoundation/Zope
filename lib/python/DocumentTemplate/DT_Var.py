#!/usr/local/bin/python 
# $What$

__doc__='''Variable insertion parameters

    When inserting variables, parameters may be specified to
    control how the data will be formatted.  In HTML source, the
    'fmt' parameter is used to specify a C-style or custom format
    to be used when inserting an object.  In EPFS source, the 'fmt'
    parameter is only used for custom formats, a C-style format is
    specified after the closing parenthesis.

    Custom formats

       A custom format is used when outputing user-defined
       objects.  The value of a custom format is a method name to
       be invoked on the object being inserted.  The method should
       return an object that, when converted to a string, yields
       the desired text.  For example, the HTML source::

          <!--#var date fmt=DayOfWeek-->

       Inserts the result of calling the method 'DayOfWeek' of the
       object bound to the variable 'date', with no arguments.

       In addition to object methods, serveral additional custom
       formats are available:

	   html-quote -- Convert characters that have special meaning
	     in HTML to HTML character entities.

	   url-quote -- Convert characters that have special meaning
	     in URLS to HTML character entities using decimal values.

	   multi-line -- Convert newlines and carriage-return and
	     newline combinations to break tags.

           whole-dollars -- Show a numeric value with a dollar symbol.

           dollar-with-commas -- Show a numeric value with a dollar
             symbol and commas showing thousands, millions, and so on.

           dollars-and-cents -- Show a numeric value with a dollar
             symbol and two decimal places.

           dollar-and-cents-with-commas -- Show a numeric value with a
	     dollar symbol and two decimal places
             and commas showing thousands, millions, and so on.

       Note that when using the EPFS source format, both a
       C-style and a custom format may be provided.  In this case,
       the C-Style format is applied to the result of calling
       the custom formatting method.

    Null values

       In some applications, and especially in database applications,
       data variables may alternate between "good" and "null" or
       "missing" values.  A format that is used for good values may be
       inappropriate for null values.  For this reason, the 'null'
       parameter can be used to specify text to be used for null
       values.  Null values are defined as values that:

         - Cannot be formatted with the specified format, and

         - Are either the special Python value 'None' or yield an
           empty string when converted to a string.

       For example, when showing a monitary value retrieved from a
       database that is either a number or a missing value, the
       following variable insertion might be used::

           <!--#var cost fmt="$%.2d" null=\'n/a\'-->

    String manipulation

       The parameters 'lower' and 'upper' may be provided to cause the
       case of the inserted text to be changed.

       The parameter 'capitalize' may be provided to cause the first
       character of the inserted value to be converted to upper case.

       The parameter 'spacify' may be provided to cause underscores in
       the inserted value to be converted to spaces.

    Truncation

       The parameters 'size' and 'etc'  can be used to truncate long
       strings.  If the 'size' parameter is specified, the string to
       be inserted is truncated at the given length.  If a space
       occurs in the second half of the truncated string, then the
       string is further truncated to the right-most space.  After
       truncation, the value given for the 'etc' parameter is added to
       the string.  If the 'etc' parameter is not provided, then '...'
       is used.  For example, if the value of spam is
       '"blah blah blah blah"', then the tag       
       '<!--#var spam size=10-->' inserts '"blah blah ..."'.
''' # '
__rcs_id__='$Id: DT_Var.py,v 1.8 1998/01/08 20:57:34 jim Exp $'

############################################################################
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
#  
#
# If you have questions regarding this software,
# contact:
#
#   Jim Fulton, jim@digicool.com
#
#   (540) 371-6909
#
############################################################################ 
__version__='$Revision: 1.8 $'[11:-2]

from DT_Util import *

from string import find, split, join

class Var: 
    name='var'
    expr=None

    def __init__(self, args, fmt=''):
	args = parse_params(args, name='', lower=1, upper=1, expr='',
			    capitalize=1, spacify=1, null='', fmt='s',
			    size=0, etc='...')
	self.args=args
	used=args.has_key

	name, expr = name_param(args,'var',1)

	self.__name__, self.expr = name, expr
	self.fmt = fmt

    def render(self, md):
	name=self.__name__
	val=self.expr
	if val is None:
	    val = md[name]
	else:
	    val=val.eval(md)

	args=self.args
	have_arg=args.has_key

	__traceback_info__=name, val, args

	# handle special formats defined using fmt= first
	if have_arg('fmt'):
	    fmt=args['fmt']
	    if hasattr(val, fmt):
		val = getattr(val,fmt)()
	    elif special_formats.has_key(fmt):
		val = special_formats[fmt](val, name, md)
	    elif fmt=='': val=''
	    else: val = fmt % val

	# next, look for upper, lower, etc
	if have_arg('upper'):
	    val = upper(val)
	if have_arg('lower'):
	    val = lower(val)
	if have_arg('capitalize'):
	    val = capitalize(val)
	if have_arg('spacify'):
	    val = gsub('_', ' ', val)

	# after this, if it's null and a null= option was given, return that
	if not val and have_arg('null'):
	    return args['null']

	# finally, pump it through the actual string format...
	val = ('%'+self.fmt) % val

	if have_arg('size'):
	    size=args['size']
	    try: size=atoi(size)
	    except: raise 'Document Error',(
		'''a <code>size</code> attribute was used in a <code>var</code>
		tag with a non-integer value.''')
	    if len(val) > size:
		val=val[:size]
		l=rfind(val,' ')
		if l > size/2:
		    val=val[:l+1]
		if have_arg('etc'): l=args['etc']
		else: l='...'
		val=val+l

	return val

    __call__=render

def html_quote(v, name='(Unknown name)', md={},
	       character_entities=(
		       (regex.compile('&'), '&amp;'),
		       (regex.compile("<"), '&lt;' ),
		       (regex.compile(">"), '&gt;' ),
		       (regex.compile('"'), '&quot;'))): #"
        text=str(v)
	for re,name in character_entities:
	    text=gsub(re,name,text)
	return text

def url_quote(v, name='(Unknown name)', md={}):
    import urllib
    return urllib.quote(str(v))

def multi_line(v, name='(Unknown name)', md={},
	       nl=regex.compile('\r?\n')):
    return gsub(nl,'<br>\n',str(v))

def whole_dollars(v, name='(Unknown name)', md={}):
    try: return "$%d" % v
    except: return ''

def dollars_and_cents(v, name='(Unknown name)', md={}):
    try: return "$%.2f" % v
    except: return ''

def commatify(v, name='(Unknown name)', md={},
	      thou=regex.compile("\([0-9]\)\([0-9][0-9][0-9]\([,.]\|$\)\)")):
    v=str(v)
    while thou.search(v) >= 0:
	v=sub(thou,"\\1,\\2",v)
    return v
    
def whole_dollars_with_commas(v, name='(Unknown name)', md={}):
    try: v= "$%d" % v
    except: v=''
    return commatify(v)

def dollars_and_cents_with_commas(v, name='(Unknown name)', md={}):
    try: v= "$%.2f" % v
    except: v= ''
    return commatify(v)

def len_format(v, name='(Unknown name)', md={}):
    return str(len(v))

def len_comma(v, name='(Unknown name)', md={}):
    return commatify(str(len(v)))

StructuredText=None
def structured_text(v, name='(Unknown name)', md={}):
    global StructuredText
    if StructuredText is None: import StructuredText
    return str(StructuredText.html_with_references(str(v), 3))

def sql_quote(v, name='(Unknown name)', md={}):
    """Quote single quotes in a string by doubling them.

    This is needed to securely insert values into sql
    string literals in templates that generate sql.
    """
    if find(v,"'") >= 0: return join(split(v,"'"),"''")
    return v

special_formats={
    'html-quote': html_quote,
    'url-quote': url_quote,
    'multi-line': multi_line,
    'comma-numeric': commatify,
    'whole-dollars': whole_dollars,
    'dollars-and-cents': dollars_and_cents,
    'dollars-with-commas': whole_dollars_with_commas,
    'dollars-and-cents-with-commas': dollars_and_cents_with_commas,
    'collection-length': len_format,
    'collection-length-with-commas': len_comma,
    'structured-text': structured_text,
    'sql-quote': sql_quote,
    }


############################################################################
# $Log: DT_Var.py,v $
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
# Added truncation support via size and etc parameters.
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
