# Package handling monstrocities

import os
import sqlwhere

# Stuff filename into the namespace so that you don't have to hard code
# this information ahead of time.  Should be portable across platforms.
sqlwhere.filename = filename = __path__[0] + os.sep + 'sql.mar'

# Yank the previous namespace in so that nothing breaks
from gadfly import *
