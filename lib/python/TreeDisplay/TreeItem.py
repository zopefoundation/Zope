
"""Tree Protocol

$Id: TreeItem.py,v 1.1 1997/09/02 20:39:52 jim Exp $"""
       

from string import join, split, rfind
from urllib import quote, unquote

# Generified example of tree support a la discussion...

class TreeProtocol:

    def tpValues(self):
	"""Return the immediate
	subobjects of the current object that should be
	shown in the tree.
	"""

    def tpId(self):
	"""Return a value to be used as an id in tree state."""
	

    def tpURL(self):
	"""Return string to be used as URL relative to parent."""
