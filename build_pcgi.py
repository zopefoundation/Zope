"""Build a PCGI

You must be in the directory containing this script.
"""
print
print '-'*78
print "Building the PCGI wrapper"

from do import *

os.chdir('pcgi')
do('./configure')
do('make')
os.chdir('..')
