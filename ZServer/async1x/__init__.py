
# We want to use updated asynchat and asyncore if using Python1.5
import sys
if sys.version[:1] < '2':
    import asyncore, asynchat
    sys.modules['asyncore']=asyncore
    sys.modules['asynchat']=asynchat
    del asyncore
    del asynchat

del sys
