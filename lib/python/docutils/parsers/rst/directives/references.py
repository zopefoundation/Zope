# Author: David Goodger, Dmitry Jemerov
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.2.10.6 $
# Date: $Date: 2005/01/07 13:26:04 $
# Copyright: This module has been placed in the public domain.

"""
Directives for references and targets.
"""

__docformat__ = 'reStructuredText'

from docutils import nodes
from docutils.transforms import references


def target_notes(name, arguments, options, content, lineno,
                 content_offset, block_text, state, state_machine):
    """Target footnote generation."""
    pending = nodes.pending(references.TargetNotes)
    state_machine.document.note_pending(pending)
    nodelist = [pending]
    return nodelist
