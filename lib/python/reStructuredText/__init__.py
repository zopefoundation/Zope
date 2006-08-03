##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Wrapper to integrate reStructuredText into Zope

This implementation requires docutils 0.3.4+ from http://docutils.sf.net/
"""

try:
    import docutils
except ImportError:
    raise ImportError, 'Please install docutils 0.3.3+ from http://docutils.sourceforge.net/#download.'

version = docutils.__version__.split('.')
if version < ['0', '3', '3']:
    raise ImportError, """Old version of docutils found:
Got: %(version)s, required: 0.3.3+
Please remove docutils from %(path)s and replace it with a new version. You
can download docutils at http://docutils.sourceforge.net/#download.
""" % {'version' : docutils.__version__, 'path' : docutils.__path__[0] }

import sys, os, locale
from App.config import getConfiguration
from docutils.core import publish_parts

# get encoding
default_enc = sys.getdefaultencoding()
default_output_encoding = getConfiguration().rest_output_encoding or default_enc
default_input_encoding = getConfiguration().rest_input_encoding or default_enc

# starting level for <H> elements (default behaviour inside Zope is <H3>)
default_level = 3
initial_header_level = getConfiguration().rest_header_level or default_level

# default language used for internal translations and language mappings for DTD
# elements
default_lang = 'en'
default_language_code = getConfiguration().rest_language_code or default_language


class Warnings:

    def __init__(self):
        self.messages = []

    def write(self, message):
        self.messages.append(message)

def render(src,
           writer='html4css1',
           report_level=1,
           stylesheet='default.css',
           input_encoding=default_input_encoding,
           output_encoding=default_output_encoding,
           language_code=default_language_code,
           initial_header_level = initial_header_level,
           settings = {}):
    """get the rendered parts of the document the and warning object
    """
    # Docutils settings:
    settings = settings.copy()
    settings['input_encoding'] = input_encoding
    settings['output_encoding'] = output_encoding
    settings['stylesheet'] = stylesheet
    if language_code:
        settings['language_code'] = language_code
    settings['language_code'] = language_code
    settings['file_insertion_enabled'] = 0
    settings['raw_enabled'] = 0
    # starting level for <H> elements:
    settings['initial_header_level'] = initial_header_level + 1
    # set the reporting level to something sane:
    settings['report_level'] = report_level
    # don't break if we get errors:
    settings['halt_level'] = 6
    # remember warnings:
    settings['warning_stream'] = warning_stream = Warnings()

    parts = publish_parts(source=src, writer_name=writer,
                          settings_overrides=settings,
                          config_section='zope application')

    return parts, warning_stream

def HTML(src,
         writer='html4css1',
         report_level=1,
         stylesheet='default.css',
         input_encoding=default_input_encoding,
         output_encoding=default_output_encoding,
         language_code=default_language_code,
         initial_header_level = initial_header_level,
         warnings = None,
         settings = {}):
    """ render HTML from a reStructuredText string 

        - 'src'  -- string containing a valid reST document

        - 'writer' -- docutils writer 

        - 'report_level' - verbosity of reST parser

        - 'stylesheet' - Stylesheet to be used

        - 'input_encoding' - encoding of the reST input string

        - 'output_encoding' - encoding of the rendered HTML output
        
        - 'report_level' - verbosity of reST parser

        - 'language_code' - docutils language
        
        - 'initial_header_level' - level of the first header tag
        
        - 'warnings' - will be overwritten with a string containing the warnings
        
        - 'settings' - dict of settings to pass in to Docutils, with priority

    """
    parts, warning_stream = render(src,
                                   writer = writer,
                                   report_level = report_level,
                                   stylesheet = stylesheet,
                                   input_encoding = input_encoding,
                                   output_encoding = output_encoding,
                                   language_code=language_code,
                                   initial_header_level = initial_header_level,
                                   settings = settings)

    header = '<h%(level)s class="title">%(title)s</h%(level)s>\n' % {
                  'level': initial_header_level,
                  'title': parts['title'],
             }

    subheader = '<h%(level)s class="subtitle">%(subtitle)s</h%(level)s>\n' % {
                  'level': initial_header_level+1,
                  'subtitle': parts['subtitle'],
             }
    
    body = '%(docinfo)s%(body)s' % {
                  'docinfo': parts['docinfo'],
                  'body': parts['body'],
             }


    output = ''
    if parts['title']:
        output = output + header
    if parts['subtitle']:
        output = output + subheader
    output = output + body

    
    warnings = ''.join(warning_stream.messages)

    return output.encode(output_encoding)

__all__ = ("HTML", 'render')
