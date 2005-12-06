# Authors: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 2321 $
# Date: $Date: 2004-06-20 14:28:08 +0200 (Sun, 20 Jun 2004) $
# Copyright: This module has been placed in the public domain.

"""
This package contains Docutils Writer modules.
"""

__docformat__ = 'reStructuredText'


import sys
import docutils
from docutils import languages, Component
from docutils.transforms import universal


class Writer(Component):

    """
    Abstract base class for docutils Writers.

    Each writer module or package must export a subclass also called 'Writer'.
    Each writer must support all standard node types listed in
    `docutils.nodes.node_class_names`.

    The `write()` method is the main entry point.
    """

    component_type = 'writer'
    config_section = 'writers'

    document = None
    """The document to write (Docutils doctree); set by `write`."""

    output = None
    """Final translated form of `document` (Unicode string);
    set by `translate`."""

    language = None
    """Language module for the document; set by `write`."""

    destination = None
    """`docutils.io` Output object; where to write the document.
    Set by `write`."""

    def __init__(self):

        # Currently only used by HTML writer for output fragments:
        self.parts = {}
        """Mapping of document part names to fragments of `self.output`.
        Values are Unicode strings; encoding is up to the client.  The 'whole'
        key should contain the entire document output.
        """

    def write(self, document, destination):
        """
        Process a document into its final form.

        Translate `document` (a Docutils document tree) into the Writer's
        native format, and write it out to its `destination` (a
        `docutils.io.Output` subclass object).

        Normally not overridden or extended in subclasses.
        """
        self.document = document
        self.language = languages.get_language(
            document.settings.language_code)
        self.destination = destination
        self.translate()
        output = self.destination.write(self.output)
        return output

    def translate(self):
        """
        Do final translation of `self.document` into `self.output` (Unicode
        string).  Called from `write`.  Override in subclasses.

        Usually done with a `docutils.nodes.NodeVisitor` subclass, in
        combination with a call to `docutils.nodes.Node.walk()` or
        `docutils.nodes.Node.walkabout()`.  The ``NodeVisitor`` subclass must
        support all standard elements (listed in
        `docutils.nodes.node_class_names`) and possibly non-standard elements
        used by the current Reader as well.
        """
        raise NotImplementedError('subclass must override this method')

    def assemble_parts(self):
        """Assemble the `self.parts` dictionary.  Extend in subclasses."""
        self.parts['whole'] = self.output


_writer_aliases = {
      'html': 'html4css1',
      'latex': 'latex2e',
      'pprint': 'pseudoxml',
      'pformat': 'pseudoxml',
      'pdf': 'rlpdf',
      'xml': 'docutils_xml',}

def get_writer_class(writer_name):
    """Return the Writer class from the `writer_name` module."""
    writer_name = writer_name.lower()
    if _writer_aliases.has_key(writer_name):
        writer_name = _writer_aliases[writer_name]
    module = __import__(writer_name, globals(), locals())
    return module.Writer
