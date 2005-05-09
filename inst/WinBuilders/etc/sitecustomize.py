""" Add Zope packages in Windows binary distro to sys.path automagically """
import sys
import os
try:
    sp = __file__
except:
    sp = None
if sp:
    dn = os.path.dirname
    swhome = os.path.join(dn(dn(dn(dn(sp)))), 'lib', 'python')
    if os.path.exists(swhome):
        sys.path.insert(0, swhome)

