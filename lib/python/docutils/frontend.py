# Author: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.5 $
# Date: $Date: 2003/08/13 16:19:29 $
# Copyright: This module has been placed in the public domain.

"""
Command-line and common processing for Docutils front-end tools.

Exports the following classes:

- `OptionParser`: Standard Docutils command-line processing.
- `Values`: Runtime settings; objects are simple structs
  (``object.attribute``).
- `ConfigParser`: Standard Docutils config file processing.
"""

__docformat__ = 'reStructuredText'

import os
import os.path
import sys
import types
import ConfigParser as CP
import codecs
import docutils
import optparse
from optparse import Values, SUPPRESS_HELP


def store_multiple(option, opt, value, parser, *args, **kwargs):
    """
    Store multiple values in `parser.values`.  (Option callback.)
    
    Store `None` for each attribute named in `args`, and store the value for
    each key (attribute name) in `kwargs`.
    """
    for attribute in args:
        setattr(parser.values, attribute, None)
    for key, value in kwargs.items():
        setattr(parser.values, key, value)

def read_config_file(option, opt, value, parser):
    """
    Read a configuration file during option processing.  (Option callback.)
    """
    config_parser = ConfigParser()
    config_parser.read(value, parser)
    settings = config_parser.get_section('options')
    make_paths_absolute(settings, parser.relative_path_settings,
                        os.path.dirname(value))
    parser.values.__dict__.update(settings)

def set_encoding(option, opt, value, parser):
    """
    Validate & set the encoding specified.  (Option callback.)
    """
    try:
        value = validate_encoding(option.dest, value)
    except LookupError, error:
        raise (optparse.OptionValueError('option "%s": %s' % (opt, error)),
               None, sys.exc_info()[2])
    setattr(parser.values, option.dest, value)

def validate_encoding(name, value):
    try:
        codecs.lookup(value)
    except LookupError:
        raise (LookupError('unknown encoding: "%s"' % value),
               None, sys.exc_info()[2])
    return value

def set_encoding_error_handler(option, opt, value, parser):
    """
    Validate & set the encoding error handler specified.  (Option callback.)
    """
    try:
        value = validate_encoding_error_handler(option.dest, value)
    except LookupError, error:
        raise (optparse.OptionValueError('option "%s": %s' % (opt, error)),
               None, sys.exc_info()[2])
    setattr(parser.values, option.dest, value)

def validate_encoding_error_handler(name, value):
    try:
        codecs.lookup_error(value)
    except AttributeError:              # prior to Python 2.3
        if value not in ('strict', 'ignore', 'replace'):
            raise (LookupError(
                'unknown encoding error handler: "%s" (choices: '
                '"strict", "ignore", or "replace")' % value),
                   None, sys.exc_info()[2])
    except LookupError:
        raise (LookupError(
            'unknown encoding error handler: "%s" (choices: '
            '"strict", "ignore", "replace", "backslashreplace", '
            '"xmlcharrefreplace", and possibly others; see documentation for '
            'the Python ``codecs`` module)' % value),
               None, sys.exc_info()[2])
    return value

def set_encoding_and_error_handler(option, opt, value, parser):
    """
    Validate & set the encoding and error handler specified.  (Option callback.)
    """
    try:
        value = validate_encoding_and_error_handler(option.dest, value)
    except LookupError, error:
        raise (optparse.OptionValueError('option "%s": %s' % (opt, error)),
               None, sys.exc_info()[2])
    if ':' in value:
        encoding, handler = value.split(':')
        setattr(parser.values, option.dest + '_error_handler', handler)
    else:
        encoding = value
    setattr(parser.values, option.dest, encoding)

def validate_encoding_and_error_handler(name, value):
    if ':' in value:
        encoding, handler = value.split(':')
        validate_encoding_error_handler(name + '_error_handler', handler)
    else:
        encoding = value
    validate_encoding(name, encoding)
    return value

def make_paths_absolute(pathdict, keys, base_path=None):
    """
    Interpret filesystem path settings relative to the `base_path` given.

    Paths are values in `pathdict` whose keys are in `keys`.  Get `keys` from
    `OptionParser.relative_path_settings`.
    """
    if base_path is None:
        base_path = os.getcwd()
    for key in keys:
        if pathdict.has_key(key) and pathdict[key]:
            pathdict[key] = os.path.normpath(
                os.path.abspath(os.path.join(base_path, pathdict[key])))


class OptionParser(optparse.OptionParser, docutils.SettingsSpec):

    """
    Parser for command-line and library use.  The `settings_spec`
    specification here and in other Docutils components are merged to build
    the set of command-line options and runtime settings for this process.

    Common settings (defined below) and component-specific settings must not
    conflict.  Short options are reserved for common settings, and components
    are restrict to using long options.
    """

    threshold_choices = 'info 1 warning 2 error 3 severe 4 none 5'.split()
    """Possible inputs for for --report and --halt threshold values."""

    thresholds = {'info': 1, 'warning': 2, 'error': 3, 'severe': 4, 'none': 5}
    """Lookup table for --report and --halt threshold values."""

    if hasattr(codecs, 'backslashreplace_errors'):
        default_error_encoding_error_handler = 'backslashreplace'
    else:
        default_error_encoding_error_handler = 'replace'

    settings_spec = (
        'General Docutils Options',
        None,
        (('Include a "Generated by Docutils" credit and link at the end '
          'of the document.',
          ['--generator', '-g'], {'action': 'store_true'}),
         ('Do not include a generator credit.',
          ['--no-generator'], {'action': 'store_false', 'dest': 'generator'}),
         ('Include the date at the end of the document (UTC).',
          ['--date', '-d'], {'action': 'store_const', 'const': '%Y-%m-%d',
                             'dest': 'datestamp'}),
         ('Include the time & date at the end of the document (UTC).',
          ['--time', '-t'], {'action': 'store_const',
                             'const': '%Y-%m-%d %H:%M UTC',
                             'dest': 'datestamp'}),
         ('Do not include a datestamp of any kind.',
          ['--no-datestamp'], {'action': 'store_const', 'const': None,
                               'dest': 'datestamp'}),
         ('Include a "View document source" link (relative to destination).',
          ['--source-link', '-s'], {'action': 'store_true'}),
         ('Use the supplied <URL> verbatim for a "View document source" '
          'link; implies --source-link.',
          ['--source-url'], {'metavar': '<URL>'}),
         ('Do not include a "View document source" link.',
          ['--no-source-link'],
          {'action': 'callback', 'callback': store_multiple,
           'callback_args': ('source_link', 'source_url')}),
         ('Enable backlinks from section headers to table of contents '
          'entries.  This is the default.',
          ['--toc-entry-backlinks'],
          {'dest': 'toc_backlinks', 'action': 'store_const', 'const': 'entry',
           'default': 'entry'}),
         ('Enable backlinks from section headers to the top of the table of '
          'contents.',
          ['--toc-top-backlinks'],
          {'dest': 'toc_backlinks', 'action': 'store_const', 'const': 'top'}),
         ('Disable backlinks to the table of contents.',
          ['--no-toc-backlinks'],
          {'dest': 'toc_backlinks', 'action': 'store_false'}),
         ('Enable backlinks from footnotes and citations to their '
          'references.  This is the default.',
          ['--footnote-backlinks'],
          {'action': 'store_true', 'default': 1}),
         ('Disable backlinks from footnotes and citations.',
          ['--no-footnote-backlinks'],
          {'dest': 'footnote_backlinks', 'action': 'store_false'}),
         ('Set verbosity threshold; report system messages at or higher than '
          '<level> (by name or number: "info" or "1", warning/2, error/3, '
          'severe/4; also, "none" or "5").  Default is 2 (warning).',
          ['--report', '-r'], {'choices': threshold_choices, 'default': 2,
                               'dest': 'report_level', 'metavar': '<level>'}),
         ('Report all system messages, info-level and higher.  (Same as '
          '"--report=info".)',
          ['--verbose', '-v'], {'action': 'store_const', 'const': 'info',
                                'dest': 'report_level'}),
         ('Do not report any system messages.  (Same as "--report=none".)',
          ['--quiet', '-q'], {'action': 'store_const', 'const': 'none',
                              'dest': 'report_level'}),
         ('Set the threshold (<level>) at or above which system messages are '
          'converted to exceptions, halting execution immediately.  Levels '
          'as in --report.  Default is 4 (severe).',
          ['--halt'], {'choices': threshold_choices, 'dest': 'halt_level',
                       'default': 4, 'metavar': '<level>'}),
         ('Same as "--halt=info": halt processing at the slightest problem.',
          ['--strict'], {'action': 'store_const', 'const': 'info',
                         'dest': 'halt_level'}),
         ('Enable a non-zero exit status for normal exit if non-halting '
          'system messages (at or above <level>) were generated.  Levels as '
          'in --report.  Default is 5 (disabled).  Exit status is the maximum '
          'system message level plus 10 (11 for INFO, etc.).',
          ['--exit'], {'choices': threshold_choices, 'dest': 'exit_level',
                       'default': 5, 'metavar': '<level>'}),
         ('Report debug-level system messages and generate diagnostic output.',
          ['--debug'], {'action': 'store_true'}),
         ('Do not report debug-level system messages or generate diagnostic '
          'output.',
          ['--no-debug'], {'action': 'store_false', 'dest': 'debug'}),
         ('Send the output of system messages (warnings) to <file>.',
          ['--warnings'], {'dest': 'warning_stream', 'metavar': '<file>'}),
         ('Enable Python tracebacks when an error occurs.',
          ['--traceback'], {'action': 'store_true', 'default': None}),
         ('Disable Python tracebacks when errors occur; report just the error '
          'instead.  This is the default.',
          ['--no-traceback'], {'dest': 'traceback', 'action': 'store_false'}),
         ('Specify the encoding of input text.  Default is locale-dependent.',
          ['--input-encoding', '-i'],
          {'action': 'callback', 'callback': set_encoding,
           'metavar': '<name>', 'type': 'string', 'dest': 'input_encoding'}),
         ('Specify the text encoding for output.  Default is UTF-8.  '
          'Optionally also specify the encoding error handler for unencodable '
          'characters (see "--error-encoding"); default is "strict".',
          ['--output-encoding', '-o'],
          {'action': 'callback', 'callback': set_encoding_and_error_handler,
           'metavar': '<name[:handler]>', 'type': 'string',
           'dest': 'output_encoding', 'default': 'utf-8'}),
         (SUPPRESS_HELP,                # usually handled by --output-encoding
          ['--output_encoding_error_handler'],
          {'action': 'callback', 'callback': set_encoding_error_handler,
           'type': 'string', 'dest': 'output_encoding_error_handler',
           'default': 'strict'}),
         ('Specify the text encoding for error output.  Default is ASCII.  '
          'Optionally also specify the encoding error handler for unencodable '
          'characters, after a colon (":").  Acceptable values are the same '
          'as for the "error" parameter of Python\'s ``encode`` string '
          'method.  Default is "%s".' % default_error_encoding_error_handler,
          ['--error-encoding', '-e'],
          {'action': 'callback', 'callback': set_encoding_and_error_handler,
           'metavar': '<name[:handler]>', 'type': 'string',
           'dest': 'error_encoding', 'default': 'ascii'}),
         (SUPPRESS_HELP,                # usually handled by --error-encoding
          ['--error_encoding_error_handler'],
          {'action': 'callback', 'callback': set_encoding_error_handler,
           'type': 'string', 'dest': 'error_encoding_error_handler',
           'default': default_error_encoding_error_handler}),
         ('Specify the language of input text (ISO 639 2-letter identifier).'
          '  Default is "en" (English).',
          ['--language', '-l'], {'dest': 'language_code', 'default': 'en',
                                 'metavar': '<name>'}),
         ('Read configuration settings from <file>, if it exists.',
          ['--config'], {'metavar': '<file>', 'type': 'string',
                         'action': 'callback', 'callback': read_config_file}),
         ("Show this program's version number and exit.",
          ['--version', '-V'], {'action': 'version'}),
         ('Show this help message and exit.',
          ['--help', '-h'], {'action': 'help'}),
         # Hidden options, for development use only:
         (SUPPRESS_HELP, ['--dump-settings'], {'action': 'store_true'}),
         (SUPPRESS_HELP, ['--dump-internals'], {'action': 'store_true'}),
         (SUPPRESS_HELP, ['--dump-transforms'], {'action': 'store_true'}),
         (SUPPRESS_HELP, ['--dump-pseudo-xml'], {'action': 'store_true'}),
         (SUPPRESS_HELP, ['--expose-internal-attribute'],
          {'action': 'append', 'dest': 'expose_internals'}),))
    """Runtime settings and command-line options common to all Docutils front
    ends.  Setting specs specific to individual Docutils components are also
    used (see `populate_from_components()`)."""

    settings_defaults = {'_disable_config': None}
    """Defaults for settings that don't have command-line option equivalents."""

    relative_path_settings = ('warning_stream',)

    version_template = '%%prog (Docutils %s)' % docutils.__version__
    """Default version message."""

    def __init__(self, components=(), defaults=None, read_config_files=None,
                 *args, **kwargs):
        """
        `components` is a list of Docutils components each containing a
        ``.settings_spec`` attribute.  `defaults` is a mapping of setting
        default overrides.
        """
        optparse.OptionParser.__init__(
            self, add_help_option=None,
            formatter=optparse.TitledHelpFormatter(width=78),
            *args, **kwargs)
        if not self.version:
            self.version = self.version_template
        # Make an instance copy (it will be modified):
        self.relative_path_settings = list(self.relative_path_settings)
        self.populate_from_components((self,) + tuple(components))
        defaults = defaults or {}
        if read_config_files and not self.defaults['_disable_config']:
            # @@@ Extract this code into a method, which can be called from
            # the read_config_file callback also.
            config = ConfigParser()
            config.read_standard_files(self)
            config_settings = config.get_section('options')
            make_paths_absolute(config_settings, self.relative_path_settings)
            defaults.update(config_settings)
        # Internal settings with no defaults from settings specifications;
        # initialize manually:
        self.set_defaults(_source=None, _destination=None, **defaults)

    def populate_from_components(self, components):
        """
        For each component, first populate from the `SettingsSpec.settings_spec`
        structure, then from the `SettingsSpec.settings_defaults` dictionary.
        After all components have been processed, check for and populate from
        each component's `SettingsSpec.settings_default_overrides` dictionary.
        """
        for component in components:
            if component is None:
                continue
            i = 0
            settings_spec = component.settings_spec
            self.relative_path_settings.extend(
                component.relative_path_settings)
            while i < len(settings_spec):
                title, description, option_spec = settings_spec[i:i+3]
                if title:
                    group = optparse.OptionGroup(self, title, description)
                    self.add_option_group(group)
                else:
                    group = self        # single options
                for (help_text, option_strings, kwargs) in option_spec:
                    group.add_option(help=help_text, *option_strings,
                                     **kwargs)
                if component.settings_defaults:
                    self.defaults.update(component.settings_defaults)
                i += 3
        for component in components:
            if component and component.settings_default_overrides:
                self.defaults.update(component.settings_default_overrides)

    def check_values(self, values, args):
        if hasattr(values, 'report_level'):
            values.report_level = self.check_threshold(values.report_level)
        if hasattr(values, 'halt_level'):
            values.halt_level = self.check_threshold(values.halt_level)
        if hasattr(values, 'exit_level'):
            values.exit_level = self.check_threshold(values.exit_level)
        values._source, values._destination = self.check_args(args)
        make_paths_absolute(values.__dict__, self.relative_path_settings,
                            os.getcwd())
        return values

    def check_threshold(self, level):
        try:
            return int(level)
        except ValueError:
            try:
                return self.thresholds[level.lower()]
            except (KeyError, AttributeError):
                self.error('Unknown threshold: %r.' % level)

    def check_args(self, args):
        source = destination = None
        if args:
            source = args.pop(0)
            if source == '-':           # means stdin
                source = None
        if args:
            destination = args.pop(0)
            if destination == '-':      # means stdout
                destination = None
        if args:
            self.error('Maximum 2 arguments allowed.')
        if source and source == destination:
            self.error('Do not specify the same file for both source and '
                       'destination.  It will clobber the source file.')
        return source, destination


class ConfigParser(CP.ConfigParser):

    standard_config_files = (
        '/etc/docutils.conf',               # system-wide
        './docutils.conf',                  # project-specific
        os.path.expanduser('~/.docutils'))  # user-specific
    """Docutils configuration files, using ConfigParser syntax (section
    'options').  Later files override earlier ones."""

    validation = {
        'options':
        {'input_encoding': validate_encoding,
         'output_encoding': validate_encoding,
         'output_encoding_error_handler': validate_encoding_error_handler,
         'error_encoding': validate_encoding,
         'error_encoding_error_handler': validate_encoding_error_handler}}
    """{section: {option: validation function}} mapping, used by
    `validate_options`.  Validation functions take two parameters: name and
    value.  They return a (possibly modified) value, or raise an exception."""

    def read_standard_files(self, option_parser):
        self.read(self.standard_config_files, option_parser)

    def read(self, filenames, option_parser):
        if type(filenames) in types.StringTypes:
            filenames = [filenames]
        for filename in filenames:
            CP.ConfigParser.read(self, filename)
            self.validate_options(filename, option_parser)

    def validate_options(self, filename, option_parser):
        for section in self.validation.keys():
            if not self.has_section(section):
                continue
            for option in self.validation[section].keys():
                if self.has_option(section, option):
                    value = self.get(section, option)
                    validator = self.validation[section][option]
                    try:
                        new_value = validator(option, value)
                    except Exception, error:
                        raise (ValueError(
                            'Error in config file "%s", section "[%s]":\n'
                            '    %s: %s\n        %s = %s'
                            % (filename, section, error.__class__.__name__,
                               error, option, value)), None, sys.exc_info()[2])
                    self.set(section, option, new_value)

    def optionxform(self, optionstr):
        """
        Transform '-' to '_' so the cmdline form of option names can be used.
        """
        return optionstr.lower().replace('-', '_')

    def get_section(self, section, raw=0, vars=None):
        """
        Return a given section as a dictionary (empty if the section
        doesn't exist).

        All % interpolations are expanded in the return values, based on the
        defaults passed into the constructor, unless the optional argument
        `raw` is true.  Additional substitutions may be provided using the
        `vars` argument, which must be a dictionary whose contents overrides
        any pre-existing defaults.

        The section DEFAULT is special.
        """
        section_dict = {}
        if self.has_section(section):
            for option in self.options(section):
                section_dict[option] = self.get(section, option, raw, vars)
        return section_dict
