"""
Object monikers

   An object moniker is an intelligent reference to a
   persistent object. A moniker can be turned back into
   a real object that retains its correct session context
   and aquisition relationships via a simple interface.

"""

__version__='$Revision: 1.1 $'[11:-2]


import Globals


class Moniker:
    """ """
    def __init__(self, obj=None, p=1):
	if obj is None: return
	self.id   =absattr(obj.id)
	self.title=absattr(obj.title)
	self.mtype=absattr(obj.meta_type)
	self.oid  =obj._p_oid
	self.jar  =obj._p_jar.name
	self.aqp  =None
	if p:
	    try:    self.aqp=Moniker(obj.aq_parent, 0)
	    except: self.aqp=None


    def bind(self):
	if self.jar is None: jar=Globals.Bobobase._jar
	else: jar=Globals.SessionBase[self.jar].jar
	obj=jar[self.oid]
	if self.aqp is not None:
	    obj=obj.__of__(self.aqp.bind())
	return obj




def absattr(attr):
    if callable(attr): return attr()
    return attr
