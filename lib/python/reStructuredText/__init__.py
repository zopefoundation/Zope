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

""" Wrapper to integrate reStructuredText into Zope """

__all__ = ("HTML", ) 

import docutils.core 
from docutils.io import StringOutput, StringInput 
import sys, os

default_input_encoding = os.environ.get("REST_INPUT_ENCODING", 
                                        sys.getdefaultencoding())
default_output_encoding = os.environ.get("REST_OUTPUT_ENCODING", 
                                         sys.getdefaultencoding())

class Warnings:

    def __init__(self):
        self.messages = []

    def write(self, message):
        self.messages.append(message)


def HTML(src, 
         writer='html4zope', 
         report_level=1, 
         stylesheet='default.css',
         input_encoding=default_input_encoding, 
         output_encoding=default_output_encoding):

    """ render HTML from a reStructuredText string 

        - 'src'  -- string containing a valid reST document

        - 'writer' -- docutils writer 

        - 'report_level' - verbosity of reST parser

        - 'stylesheet' - Stylesheet to be used

        - 'input_encoding' - encoding of the reST input string

        - 'output_encoding' - encoding of the rendered HTML output
    """

    pub = docutils.core.Publisher()
    pub.set_reader('standalone', None, 'restructuredtext')
    pub.set_writer(writer)

    # go with the defaults
    pub.get_settings()

    pub.settings.stylesheet = stylesheet

    # this is needed, but doesn't seem to do anything
    pub.settings._destination = ''

    # set the reporting level to something sane
    pub.settings.report_level = report_level

    # don't break if we get errors
    pub.settings.halt_level = 6

    # remember warnings
    pub.settings.warning_stream = Warnings()

    # input
    pub.source = StringInput(source=src, encoding=input_encoding)

    # output - not that it's needed
    pub.destination = StringOutput(encoding=output_encoding)

    # parse!
    document = pub.reader.read(pub.source, pub.parser, pub.settings)

    # transform
    pub.apply_transforms(document)
    
    warnings = ''.join(pub.settings.warning_stream.messages)

    # do the format
    return pub.writer.write(document, pub.destination)



from docutils import writers
import html4zope

writers.html4zope = html4zope
sys.modules['docutils.writers.html4zope'] = html4zope
