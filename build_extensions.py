"""Build the Zope Extension Modules

You must be in the directory containing this script.
"""

from do import *

print
print '-'*78
print 'Building extension modules'

make('lib','python')
make('lib','python','DocumentTemplate')
make('lib','python','BoboPOS')
