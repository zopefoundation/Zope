"""Build a PCGI

You must be in the directory containing this script.
"""

from do import *

os.chdir('pcgi')
do('./configure')
do('make')
os.chdir('..')
