
'''Inserting equality comparisons with 'sqltest'

    The 'sqltest' tag is used to insert SQL source to test whether
    an SQL column is equal to a value given in a DTML variable.

    The 'sqltest' tag has the following attributes:

      name -- The name of the variable to insert. As with other
              DTML tags, the 'name=' prefix may be, and usually is,
              ommitted.

      type -- The data type of the value to be inserted.  This
	      attribute is required and may be one of 'string',
	      'int', 'float', or 'nb'.  The 'nb' data type indicates a
	      string that must have a length that is greater than 0.

      column -- The name of the SQL column, if different than 'name'.

      multiple -- A flag indicating whether multiple values may be
		  provided.

      optional -- A flag indicating if the test is optional.
		  If the test is optinal and no value is provided for
		  a variable, or the value provided is an invalid
		  empty string, then no text is inserted.
      

    For example, given the tag::

      <!--#sqltest color column=color_name type=nb multiple-->

    If the value of the color variable is '"red"', then the following
    test is inserted::

      column_name = 'red'

    If a list of values is givem, such as: '"red"', '"pink"', and
    '"purple"', then an SQL 'in' test is inserted:
    
      column_name = in ('red', 'pink', 'purple')

'''

############################################################################
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################ 
__rcs_id__='$Id: sqlgroup.py,v 1.1 1998/03/17 19:31:22 jim Exp $'
__version__='$Revision: 1.1 $'[11:-2]

from DocumentTemplate.DT_Util import *
from string import strip, join
import sys

class SQLGroup:
    blockContinuations='and','or'
    name='sqlgroup'

    def __init__(self, blocks):

	self.blocks=blocks
	tname, args, section = blocks[0]
	self.__name__=args or tname

    def render(self,md):

	r=[]
	for tname, args, section in self.blocks:
	    __traceback_info__=tname
	    s=strip(section(None, md))
	    if s:
		if r: r.append(tname)
		r.append("%s\n" % s)
		
	if r:
	    if len(r) > 1: return "(%s)\n" % join(r,' ')
	    return r[0] 

	return ''

    __call__=render

##########################################################################
#
# $Log: sqlgroup.py,v $
# Revision 1.1  1998/03/17 19:31:22  jim
# added new sql tags
#
#
