##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
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

           'whole-dollars' -- Show a numeric value with a dollar symbol.

           'dollars-and-cents' -- Show a numeric value with a dollar
             symbol and two decimal places.

           'collection-length' -- Get the length of a collection of objects.

       Note that when using the EPFS source format, both a
       C-style and a custom format may be provided.  In this case,
       the C-Style format is applied to the result of calling
       the custom formatting method.

    Null values and missing variables

       In some applications, and especially in database applications,
       data variables may alternate between "good" and "null" or
       "missing" values.  A format that is used for good values may be
       inappropriate for null values.  For this reason, the 'null'
       parameter can be used to specify text to be used for null
       values.  Null values are defined as values that:

         - Cannot be formatted with the specified format, and

         - Are either the special Python value 'None' or 
           are false and yield an empty string when converted to
           a string.

       For example, when showing a monitary value retrieved from a
       database that is either a number or a missing value, the
       following variable insertion might be used::

           <dtml-var cost fmt="$%.2d" null=\'n/a\'>

       Missing values are providing for variables which are not
       present in the name space, rather than raising an NameError,
       you could do this:

           <dtml-var cost missing=0>

       and in this case, if cost was missing, it would be set to 0.
       In the case where you want to deal with both at the same time,
       you can use 'default':

           <dtml-var description default=''>

       In this case, it would use '' if the value was null or if the
       variable was missing.

    String manipulation

       A number of special attributes are provided to transform the
       value after formatting has been applied.  These parameters
       are supplied without arguments.

       'lower' --  cause all upper-case letters to be converted to lower case. 

       'upper' --  cause all upper-case letters to be converted to lower case. 

       'capitalize' -- cause the first character of the inserted value
       to be converted to upper case. 

       'spacify' -- cause underscores in the inserted value to be
       converted to spaces.

       'thousands_commas' -- cause commas to be inserted every three
       digits to the left of a decimal point in values containing
       numbers.  For example, the value, "12000 widgets" becomes
       "12,000 widgets".

       'html_quote' -- convert characters that have special meaning
       in HTML to HTML character entities.

       'url_quote' -- convert characters that have special meaning
       in URLS to HTML character entities using decimal values.

       'url_quote_plus' -- like url_quote but also replace blank
       space characters with '+'. This is needed for building
       query strings in some cases.

       'sql_quote' -- Convert single quotes to pairs of single
       quotes. This is needed to safely include values in
       Standard Query Language (SQL) strings.

       'newline_to_br' -- Convert newlines and carriage-return and
       newline combinations to break tags.

       'url' -- Get the absolute URL of the object by calling it\'s
       'absolute_url' method, if it has one.

    Truncation

       The attributes 'size' and 'etc'  can be used to truncate long
       strings.  If the 'size' attribute is specified, the string to
       be inserted is truncated at the given length.  If a space
       occurs in the second half of the truncated string, then the
       string is further truncated to the right-most space.  After
       truncation, the value given for the 'etc' attribute is added to
       the string.  If the 'etc' attribute is not provided, then '...'
       is used.  For example, if the value of spam is
       '"blah blah blah blah"', then the tag       
       '<!--#var spam size=10-->' inserts '"blah blah ..."'.


Evaluating expressions without rendering results

   A 'call' tag is provided for evaluating named objects or expressions
   without rendering the result.
   

''' # '
__rcs_id__='$Id: DT_Var.py,v 1.48 2001/11/09 19:13:52 andreasjung Exp $'
__version__='$Revision: 1.48 $'[11:-2]

from DT_Util import parse_params, name_param, str
import re, string, sys
from urllib import quote, quote_plus
from cgi import escape
from html_quote import html_quote # for import by other modules, dont remove!
from types import StringType
from Acquisition import aq_base

class Var: 
    name='var'
    expr=None

    def __init__(self, args, fmt='s'):
        if args[:4]=='var ': args=args[4:]
        args = parse_params(args, name='', lower=1, upper=1, expr='',
                            capitalize=1, spacify=1, null='', fmt='s',
                            size=0, etc='...', thousands_commas=1,
                            html_quote=1, url_quote=1, sql_quote=1,
                            url_quote_plus=1, missing='',
                            newline_to_br=1, url=1)
        self.args=args
        
        self.modifiers=tuple(
            map(lambda t: t[1],
                filter(lambda m, args=args, used=args.has_key:
                       used(m[0]) and args[m[0]],
                       modifiers)))

        name, expr = name_param(args,'var',1)

        self.__name__, self.expr = name, expr
        self.fmt = fmt

        if len(args)==1 and fmt=='s':
            if expr is None: expr=name
            else: expr=expr.eval
            self.simple_form=('v', expr)
        elif len(args)==2  and fmt=='s' and args.has_key('html_quote'):
            if expr is None: expr=name
            else: expr=expr.eval
            self.simple_form=('v', expr, 'h')

    def render(self, md):
        args=self.args
        have_arg=args.has_key
        name=self.__name__

        val=self.expr

        if val is None:
            if md.has_key(name):
                if have_arg('url'):
                    val=md.getitem(name,0)
                    val=val.absolute_url()
                else:
                    val = md[name]
            else:
                if have_arg('missing'):
                    return args['missing']
                else:
                    raise KeyError, name
        else:
            val=val.eval(md)
            if have_arg('url'): val=val.absolute_url()

        __traceback_info__=name, val, args

        if have_arg('null') and not val and val != 0:
            # check for null (false but not zero, including None, [], '')
            return args['null']
            

        # handle special formats defined using fmt= first
        if have_arg('fmt'):
            _get = getattr(md, 'guarded_getattr', None)
            if _get is None:
                _get = getattr

            fmt=args['fmt']
            if have_arg('null') and not val and val != 0:
                try:
                    if hasattr(val, fmt):
                        val = _get(val, fmt)()
                    elif special_formats.has_key(fmt):
                        val = special_formats[fmt](val, name, md)
                    elif fmt=='': val=''
                    else: val = fmt % val
                except:
                    t, v= sys.exc_type, sys.exc_value
                    if hasattr(sys, 'exc_info'): t, v = sys.exc_info()[:2]
                    if val is None or not str(val): return args['null']
                    raise t, v

            else:
                # We duplicate the code here to avoid exception handler
                # which tends to screw up stack or leak
                if hasattr(val, fmt):
                    val = _get(val, fmt)()
                elif special_formats.has_key(fmt):
                    val = special_formats[fmt](val, name, md)
                elif fmt=='': val=''
                else: val = fmt % val

        # finally, pump it through the actual string format...
        fmt=self.fmt
        if fmt=='s': val=str(val)
        else: val = ('%'+self.fmt) % (val,)

        # next, look for upper, lower, etc
        for f in self.modifiers: val=f(val)

        if have_arg('size'):
            size=args['size']
            try: size=int(size)
            except: raise 'Document Error',(
                '''a <code>size</code> attribute was used in a <code>var</code>
                tag with a non-integer value.''')
            if len(val) > size:
                val=val[:size]
                l=val.rfind(' ')
                if l > size/2:
                    val=val[:l+1]
                if have_arg('etc'): l=args['etc']
                else: l='...'
                val=val+l

        return val

    __call__=render

class Call: 
    name='call'
    expr=None

    def __init__(self, args):
        args = parse_params(args, name='', expr='')
        name, expr = name_param(args,'call',1)
        if expr is None: expr=name
        else: expr=expr.eval
        self.simple_form=('i', expr, None)


def url_quote(v, name='(Unknown name)', md={}):
    return quote(str(v))

def url_quote_plus(v, name='(Unknown name)', md={}):
    return quote_plus(str(v))


def newline_to_br(v, name='(Unknown name)', md={}):
    v=str(v)
    if v.find('\r') >= 0: v=''.join(v.split('\r'))
    if v.find('\n') >= 0: v='<br>\n'.join(v.split('\n'))
    return v

def whole_dollars(v, name='(Unknown name)', md={}):
    try: return "$%d" % v
    except: return ''

def dollars_and_cents(v, name='(Unknown name)', md={}):
    try: return "$%.2f" % v
    except: return ''

def thousands_commas(v, name='(Unknown name)', md={},
                     thou=re.compile(
                         r"([0-9])([0-9][0-9][0-9]([,.]|$))").search):
    v=str(v)
    vl=v.split('.')
    if not vl: return v
    v=vl[0]
    del vl[0]
    if vl: s='.'+'.'.join(vl)
    else: s=''
    mo=thou(v)
    while mo is not None:
        l = mo.start(0)
        v=v[:l+1]+','+v[l+1:]
        mo=thou(v)
    return v+s
    
def whole_dollars_with_commas(v, name='(Unknown name)', md={}):
    try: v= "$%d" % v
    except: v=''
    return thousands_commas(v)

def dollars_and_cents_with_commas(v, name='(Unknown name)', md={}):
    try: v= "$%.2f" % v
    except: v= ''
    return thousands_commas(v)

def len_format(v, name='(Unknown name)', md={}):
    return str(len(v))

def len_comma(v, name='(Unknown name)', md={}):
    return thousands_commas(str(len(v)))

StructuredText=None
def structured_text(v, name='(Unknown name)', md={}):
    global StructuredText
    if StructuredText is None: 
        from StructuredText.StructuredText import HTML

    if isinstance(v,StringType): txt = v

    elif aq_base(v).meta_type in ['DTML Document','DTML Method']:
        txt = aq_base(v).read_raw()

    else: txt = str(v)
        
    return HTML(txt,level=3,header=0)
        

def sql_quote(v, name='(Unknown name)', md={}):
    """Quote single quotes in a string by doubling them.

    This is needed to securely insert values into sql
    string literals in templates that generate sql.
    """
    if v.find("'") >= 0: return "''".join(v.split("'"))
    return v

special_formats={
    'whole-dollars': whole_dollars,
    'dollars-and-cents': dollars_and_cents,
    'collection-length': len_format,
    'structured-text': structured_text,

    # The rest are deprecated:
    'sql-quote': sql_quote,
    'html-quote': html_quote,
    'url-quote': url_quote,
    'url-quote-plus': url_quote_plus,
    'multi-line': newline_to_br,
    'comma-numeric': thousands_commas,
    'dollars-with-commas': whole_dollars_with_commas,
    'dollars-and-cents-with-commas': dollars_and_cents_with_commas,
    }

def spacify(val):
    if val.find('_') >= 0: val=" ".join(val.split('_'))
    return val

modifiers=(html_quote, url_quote, url_quote_plus, newline_to_br,
           string.lower, string.upper, string.capitalize, spacify,
           thousands_commas, sql_quote)
modifiers=map(lambda f: (f.__name__, f), modifiers)

class Comment:
    '''Comments

    The 'comment' tag can be used to simply include comments
    in DTML source.
    
    For example::
    
      <!--#comment-->
      
        This text is not rendered.

      <!--#/comment-->
    ''' 
    name='comment'
    blockContinuations=()

    def __init__(self, args, fmt=''): pass

    def render(self, md):
        return ''

    __call__=render
