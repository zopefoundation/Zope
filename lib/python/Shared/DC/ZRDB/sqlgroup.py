
'''Inserting optional tests with 'sqlgroup'
  
    It is sometimes useful to make inputs to an SQL statement
    optinal.  Doing so can be difficult, because not only must the
    test be inserted conditionally, but SQL boolean operators may or
    may not need to be inserted depending on whether other, possibly
    optional, comparisons have been done.  The 'sqlgroup' tag
    automates the conditional insertion of boolean operators.  

    The 'sqlgroup' tag is a block tag. It can
    have any number of 'and' and 'or' continuation tags.

    The 'sqlgroup' tag has an optional attribure, 'required' to
    specify groups that must include at least one test.  This is
    useful when you want to make sure that a query is qualified, but
    want to be very flexible about how it is qualified. 

    Suppose we want to find people with a given first or nick name,
    city or minimum and maximum age.  Suppose we want all inputs to be
    optional, but want to require *some* input.  We can
    use DTML source like the following::

      <!--#sqlgroup required-->
        <!--#sqlgroup-->
          <!--#sqltest name column=nick_name type=nb multiple optional-->
        <!--#or-->
          <!--#sqltest name column=first_name type=nb multiple optional-->
	<!--#/sqlgroup-->
      <!--#and-->
	<!--#sqltest home_town type=nb optional-->
      <!--#and-->
        <!--#if minimum_age-->
	   age >= <!--#sqlvar minimum_age type=int-->
	<!--#/if-->
      <!--#and-->
        <!--#if maximum_age-->
	   age <= <!--#sqlvar maximum_age type=int-->
	<!--#/if-->
      <!--#/sqlgroup-->

    This example illustrates how groups can be nested to control
    boolean evaluation order.  It also illustrates that the grouping
    facility can also be used with other DTML tags like 'if' tags.

    The 'sqlgroup' tag checks to see if text to be inserted contains
    other than whitespace characters.  If it does, then it is inserted
    with the appropriate boolean operator, as indicated by use of an
    'and' or 'or' tag, otherwise, no text is inserted.
'''

############################################################################
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################ 
__rcs_id__='$Id: sqlgroup.py,v 1.4 1998/09/04 20:45:02 jim Exp $'
__version__='$Revision: 1.4 $'[11:-2]

from DocumentTemplate.DT_Util import parse_params
str=__builtins__['str']
from string import strip, join
import sys

class SQLGroup:
    blockContinuations='and','or'
    name='sqlgroup'
    required=None
    where=None

    def __init__(self, blocks):

	self.blocks=blocks
	tname, args, section = blocks[0]
	self.__name__="%s %s" % (tname, args)
	args = parse_params(args, required=1, where=1)
	if args.has_key(''): args[args['']]=1
	if args.has_key('required'): self.required=args['required']
	if args.has_key('where'): self.where=args['where']

    def render(self,md):

	r=[]
	for tname, args, section in self.blocks:
	    __traceback_info__=tname
	    s=strip(section(None, md))
	    if s:
		if r: r.append(tname)
		r.append("%s\n" % s)
		
	if r:
	    if len(r) > 1: r="(%s)\n" % join(r,' ')
	    else: r=r[0]
	    if self.where: r="where\n"+r
	    return r

	if self.required:
	    raise 'Input Error', 'Not enough input was provided!<p>'

	return ''

    __call__=render

##########################################################################
#
# $Log: sqlgroup.py,v $
# Revision 1.4  1998/09/04 20:45:02  jim
# fixed namespace screw up due to from DT_Util import *
#
# Revision 1.3  1998/04/02 21:33:38  jim
# Added where attribute.
#
# Revision 1.2  1998/03/18 23:25:55  jim
# Added 'required' attribute (and fixed doc).
#
# Revision 1.1  1998/03/17 19:31:22  jim
# added new sql tags
#
#
