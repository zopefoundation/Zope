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
'''
__rcs_id__='$Id: DT_Var.py,v 1.1 1997/08/27 18:55:44 jim Exp $'

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
__version__='$Revision: 1.1 $'[11:-2]

from DT_Util import *

class Var: 
    name='var'

    def __init__(self, args, fmt=''):
	args = parse_params(args, name='', lower=1, upper=1,
			    capitalize=1, spacify=1, null='', fmt='s')
	self.args=args

	if args.has_key('name'):
	    name=args
	    if args.has_key(''):
		raise ParseError, 'Two named given in var'
	elif args.has_key(''):
	    name=args['']
	else:
	    raise ParseError, 'No name given in var'

	self.__name__ = name
	self.fmt = fmt

    def render(self, md):
	name=self.__name__
	val = md[name]
	__traceback_info__=name, val

	# handle special formats defined using fmt= first
	if self.args.has_key('fmt'):
	    try:
		# first try a parameterless method of val
		val = getattr(val,self.args['fmt'])()
	    except AttributeError:
		try:
		    # failing that, try a special format
		    val = special_formats[self.args['fmt']](val)
		except KeyError:
		    try:
			# last chance - a format string itself?
			val = self.args['fmt'] % val
		    except:
			pass

	# next, look for upper, lower, etc
	if self.args.has_key('upper'):
	    val = upper(val)
	if self.args.has_key('lower'):
	    val = lower(val)
	if self.args.has_key('capitalize'):
	    val = capitalize(val)
	if self.args.has_key('spacify'):
	    val = gsub('_', ' ', val)

	# after this, if it's null and a null= option was given, return that
	if not val and self.args.has_key('null'):
	    return self.args['null']

	# finally, pump it through the actual string format...
	return ('%'+self.fmt) % val

    __call__=render

def html_quote(v,
	       character_entities=(
		       (regex.compile('&'), '&amp;'),
		       (regex.compile("<"), '&lt;' ),
		       (regex.compile(">"), '&gt;' ),
		       (regex.compile('"'), '&quot;'))): #"
        text=str(v)
	for re,name in character_entities:
	    text=gsub(re,name,text)
	return text

def url_quote(v):
    import urllib
    return urllib.quote(str(v))

def multi_line(v, nl=regex.compile('\r?\n')):
    return gsub(nl,'<br>\n',str(v))

def whole_dollars(v):
    try: return "$%d" % v
    except: return ''

def dollars_and_cents(v):
    try: return "$%.2f" % v
    except: return ''

def commatify(v,thou=regex.compile("\([0-9]\)\([0-9][0-9][0-9]\([,.]\|$\)\)")):
    v=str(v)
    while thou.search(v) >= 0:
	v=sub(thou,"\\1,\\2",v)
    return v
    
def whole_dollars_with_commas(v):
    try: v= "$%d" % v
    except: v=''
    return commatify(v)

def dollars_and_cents_with_commas(v):
    try: v= "$%.2f" % v
    except: v= ''
    return commatify(v)

special_formats={
    'html-quote': html_quote,
    'url-quote': url_quote,
    'multi-line': multi_line,
    'whole-dollars': whole_dollars,
    'dollars-and-cents': dollars_and_cents,
    'dollars-with-commas': whole_dollars_with_commas,
    'dollars-and-cents-with-commas': dollars_and_cents_with_commas,
    }

############################################################################
# $Log: DT_Var.py,v $
# Revision 1.1  1997/08/27 18:55:44  jim
# initial
#
#
