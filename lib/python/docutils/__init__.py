# Author: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.3 $
# Date: $Date: 2003/07/10 15:49:30 $
# Copyright: This module has been placed in the public domain.

"""
This is the Docutils (Python Documentation Utilities) package.

Package Structure
=================

Modules:

- __init__.py: Contains the package docstring only (this text).

- core.py: Contains the ``Publisher`` class and ``publish()`` convenience
  function.

- frontend.py: Command-line and common processing for Docutils front-ends.

- io.py: Provides a uniform API for low-level input and output.

- nodes.py: Docutils document tree (doctree) node class library.

- statemachine.py: A finite state machine specialized for
  regular-expression-based text filters.

- urischemes.py: Contains a complete mapping of known URI addressing
  scheme names to descriptions.

- utils.py: Contains the ``Reporter`` system warning class and miscellaneous
  utilities.

Subpackages:

- languages: Language-specific mappings of terms.

- parsers: Syntax-specific input parser modules or packages.

- readers: Context-specific input handlers which understand the data
  source and manage a parser.

- transforms: Modules used by readers and writers to modify DPS
  doctrees.

- writers: Format-specific output translators.
"""

__docformat__ = 'reStructuredText'

__version__ = '0.3.0'
"""``major.minor.micro`` version number.  The micro number is bumped any time
there's a change in the API incompatible with one of the front ends.  The
minor number is bumped whenever there is a project release.  The major number
will be bumped when the project is feature-complete, and perhaps if there is a
major change in the design."""


class ApplicationError(StandardError): pass
class DataError(ApplicationError): pass


class SettingsSpec:

    """
    Runtime setting specification base class.

    SettingsSpec subclass objects used by `docutils.frontend.OptionParser`.
    """

    settings_spec = ()
    """Runtime settings specification.  Override in subclasses.

    Specifies runtime settings and associated command-line options, as used by
    `docutils.frontend.OptionParser`.  This tuple contains one or more sets of
    option group title, description, and a list/tuple of tuples: ``('help
    text', [list of option strings], {keyword arguments})``.  Group title
    and/or description may be `None`; no group title implies no group, just a
    list of single options.  Runtime settings names are derived implicitly
    from long option names ("--a-setting" becomes ``settings.a_setting``) or
    explicitly from the "dest" keyword argument."""

    settings_defaults = None
    """A dictionary of defaults for internal or inaccessible (by command-line
    or config file) settings.  Override in subclasses."""

    settings_default_overrides = None
    """A dictionary of auxiliary defaults, to override defaults for settings
    defined in other components.  Override in subclasses."""

    relative_path_settings = ()
    """Settings containing filesystem paths.  Override in subclasses.

    Settings listed here are to be interpreted relative to the current working
    directory."""


class TransformSpec:

    """
    Runtime transform specification base class.

    TransformSpec subclass objects used by `docutils.transforms.Transformer`.
    """

    default_transforms = ()
    """Transforms required by this class.  Override in subclasses."""


class Component(SettingsSpec, TransformSpec):

    """Base class for Docutils components."""

    component_type = None
    """Override in subclasses."""

    supported = ()
    """Names for this component.  Override in subclasses."""

    def supports(self, format):
        """
        Is `format` supported by this component?

        To be used by transforms to ask the dependent component if it supports
        a certain input context or output format.
        """
        return format in self.supported
