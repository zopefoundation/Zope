
"""Tree Protocol

$Id: TreeItem.py,v 1.2 1998/06/08 13:34:01 brian Exp $"""
       

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
        """Return string to be used as URL relative to parent.
        The tree tag accumulates the tpURL of objects as it
        traverses the tree. At any given point during dtml
        rendering within the tree tag, you can use::
        <!--#var tree-item-url-->
        to get the url up to the point of the current object
        being rendered.
        """

        
	root=md['tree-root-url']
	"""Return string to be used as URL relative to parent."""
