"""
Object monikers

   An object moniker is an intelligent reference to a
   persistent object. A moniker can be turned back into
   a real object that retains its correct session context
   and aquisition relationships via a simple interface.

"""

__version__='$Revision: 1.4 $'[11:-2]


import Globals

class Moniker:
    """ """
    def __init__(self, obj=None, op=0):
	if obj is None: return
	pd=[]
	ob=obj
	while 1:
	    if not hasattr(ob, '_p_oid'):
		break
	    pd.append(ob._p_oid)
	    if not hasattr(ob, 'aq_parent'):
		break
	    ob=ob.aq_parent
	pd.reverse()

	self.pd=pd
	self.jr=obj._p_jar.name
	self.op=op

    def id(self):
	return absattr(self.bind().id)

    def mtype(self):
	return absattr(self.bind().meta_type)

    def assert(self):
	# Return true if the named object exists
	if self.jr is None: jar=Globals.Bobobase._jar
	else: jar=Globals.SessionBase[self.jr].jar
	for n in self.pd:
	    if not jar.has_key(n):
		return 0
	return 1

    def bind(self):
	# Return the real object named by this moniker
	if self.jr is None: jar=Globals.Bobobase._jar
	else: jar=Globals.SessionBase[self.jr].jar
	ob=None
	for n in self.pd:
	    o=jar[n]
	    if ob is not None:
		o=o.__of__(ob)
	    ob=o
	return ob

    def exact(self, other):
	# Check against another moniker to see if it
	# refers to the exact same object in the exact
	# same acquisition context.
	return self.jr==other.jr and self.pd==other.pd



def absattr(attr):
    if callable(attr): return attr()
    return attr
