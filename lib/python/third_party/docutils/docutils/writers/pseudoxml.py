# Authors: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.1.4.1 $
# Date: $Date: 2004/10/29 19:08:25 $
# Copyright: This module has been placed in the public domain.

"""
Simple internal document tree Writer, writes indented pseudo-XML.
"""

__docformat__ = 'reStructuredText'


from docutils import writers


class Writer(writers.Writer):

    supported = ('pprint', 'pformat', 'pseudoxml')
    """Formats this writer supports."""

    config_section = 'pseudoxml writer'
    config_section_dependencies = ('writers',)

    output = None
    """Final translated form of `document`."""

    def translate(self):
        self.output = self.document.pformat()

    def supports(self, format):
        """This writer supports all format-specific elements."""
        return 1
