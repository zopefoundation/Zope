# Author: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 853 $
# Date: $Date: 2002-10-24 02:51:10 +0200 (Thu, 24 Oct 2002) $
# Copyright: This module has been placed in the public domain.

"""
Docutils component-related transforms.
"""

__docformat__ = 'reStructuredText'

import sys
import os
import re
import time
from docutils import nodes, utils
from docutils import ApplicationError, DataError
from docutils.transforms import Transform, TransformError


class Filter(Transform):

    """
    Include or exclude elements which depend on a specific Docutils component.

    For use with `nodes.pending` elements.  A "pending" element's dictionary
    attribute ``details`` must contain the keys "component" and "format".  The
    value of ``details['component']`` must match the type name of the
    component the elements depend on (e.g. "writer").  The value of
    ``details['format']`` is the name of a specific format or context of that
    component (e.g. "html").  If the matching Docutils component supports that
    format or context, the "pending" element is replaced by the contents of
    ``details['nodes']`` (a list of nodes); otherwise, the "pending" element
    is removed.

    For example, the reStructuredText "meta" directive creates a "pending"
    element containing a "meta" element (in ``pending.details['nodes']``).
    Only writers (``pending.details['component'] == 'writer'``) supporting the
    "html" format (``pending.details['format'] == 'html'``) will include the
    "meta" element; it will be deleted from the output of all other writers.
    """

    default_priority = 780

    def apply(self):
        pending = self.startnode
        component_type = pending.details['component'] # 'reader' or 'writer'
        format = pending.details['format']
        component = self.document.transformer.components[component_type]
        if component.supports(format):
            pending.parent.replace(pending, pending.details['nodes'])
        else:
            pending.parent.remove(pending)
