# Author: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.2.10.6 $
# Date: $Date: 2005/01/07 13:26:05 $
# Copyright: This module has been placed in the public domain.

"""
Standalone file Reader for the reStructuredText markup syntax.
"""

__docformat__ = 'reStructuredText'


import sys
from docutils import frontend, readers
from docutils.transforms import frontmatter, references


class Reader(readers.Reader):

    supported = ('standalone',)
    """Contexts this reader supports."""

    document = None
    """A single document tree."""

    settings_spec = (
        'Standalone Reader',
        None,
        (('Disable the promotion of a lone top-level section title to '
          'document title (and subsequent section title to document '
          'subtitle promotion; enabled by default).',
          ['--no-doc-title'],
          {'dest': 'doctitle_xform', 'action': 'store_false', 'default': 1,
           'validator': frontend.validate_boolean}),
         ('Disable the bibliographic field list transform (enabled by '
          'default).',
          ['--no-doc-info'],
          {'dest': 'docinfo_xform', 'action': 'store_false', 'default': 1,
           'validator': frontend.validate_boolean}),))

    config_section = 'standalone reader'
    config_section_dependencies = ('readers',)

    default_transforms = (references.Substitutions,
                          frontmatter.DocTitle,
                          frontmatter.DocInfo,
                          references.ChainedTargets,
                          references.AnonymousHyperlinks,
                          references.IndirectHyperlinks,
                          references.Footnotes,
                          references.ExternalTargets,
                          references.InternalTargets,)
