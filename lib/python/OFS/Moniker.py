"""Object monikers

   An object moniker is an intelligent reference to a
   persistent object. A moniker can be turned back into
   a real object that retains its correct session context
   and aquisition relationships via a simple interface.

"""
__version__='$Revision: 1.5 $'[11:-2]


import Globals

class Moniker:
    """ """
    def __init__(self, ob=None):
	if ob is None: return
        self.jar=ob._p_jar.name
        self.ids=[]
	while 1:
	    if not hasattr(ob, '_p_oid'):
		break
	    self.ids.append(ob._p_oid)
	    if not hasattr(ob, 'aq_parent'):
		break
	    ob=ob.aq_parent
	self.ids.reverse()

    def id(self):
	return absattr(self.bind().id)

    def mtype(self):
	return absattr(self.bind().meta_type)

    def assert(self):
	# Return true if the named object exists
	if self.jar is None: jar=Globals.Bobobase._jar
	else: jar=Globals.SessionBase[self.jar].jar
	for n in self.ids:
	    if not jar.has_key(n):
		return 0
	return 1

    def bind(self):
	# Return the real object named by this moniker
	if self.jar is None: jar=Globals.Bobobase._jar
	else: jar=Globals.SessionBase[self.jar].jar
	ob=None
	for n in self.ids:
	    o=jar[n]
	    if ob is not None:
		o=o.__of__(ob)
	    ob=o
	return ob

    def exact(self, ob):
	# Check against another moniker to see if it
	# refers to the exact same object in the exact
	# same acquisition context.
	return self.jar==ob.jar and self.ids==ob.ids



def absattr(attr):
    if callable(attr): return attr()
    return attr




############################################################################## 
#
# $Log: Moniker.py,v $
# Revision 1.5  1998/08/14 16:46:36  brian
# Added multiple copy, paste, rename
#
