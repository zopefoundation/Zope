from pprint import pprint
from MultiMapping import *

m=MultiMapping()

m.push({'spam':1, 'eggs':2})

print m['spam']
print m['eggs']

m.push({'spam':3})

print m['spam']
print m['eggs']

pprint(m.pop())
pprint(m.pop())

try:
    print m.pop()
    raise "That\'s odd", "This last pop should have failed!"
except: # I should probably raise a specific error in this case.
    pass
