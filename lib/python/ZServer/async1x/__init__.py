
# We want to use updated asynchat and asyncore if using Python1.5
import sys
if sys.version[:1] < '2':
    import asyncore
    sys.modules['asyncore']=asyncore
    del asyncore

del sys
