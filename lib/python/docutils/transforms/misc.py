# Author: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.5 $
# Date: $Date: 2003/11/30 15:06:09 $
# Copyright: This module has been placed in the public domain.

"""
Miscellaneous transforms.
"""

__docformat__ = 'reStructuredText'

from docutils import nodes
from docutils.transforms import Transform, TransformError


class CallBack(Transform):

    """
    Inserts a callback into a document.  The callback is called when the
    transform is applied, which is determined by its priority.

    For use with `nodes.pending` elements.  Requires a ``details['callback']``
    entry, a bound method or function which takes one parameter: the pending
    node.  Other data can be stored in the ``details`` attribute or in the
    object hosting the callback method.
    """

    default_priority = 990

    def apply(self):
        pending = self.startnode
        pending.details['callback'](pending)
        pending.parent.remove(pending)


class ClassAttribute(Transform):

    default_priority = 210

    def apply(self):
        pending = self.startnode
        class_value = pending.details['class']
        parent = pending.parent
        child = pending
        while parent:
            for index in range(parent.index(child) + 1, len(parent)):
                element = parent[index]
                if isinstance(element, nodes.comment):
                    continue
                element.set_class(class_value)
                pending.parent.remove(pending)
                return
            else:
                child = parent
                parent = parent.parent
        error = self.document.reporter.error(
            'No suitable element following "%s" directive'
            % pending.details['directive'],
            nodes.literal_block(pending.rawsource, pending.rawsource),
            line=pending.line)
        pending.parent.replace(pending, error)
