# Author: Andreas Jung
# Contact: andreas@andreas-jung.com
# Revision: $Revision: 1.3 $
# Date: $Date: 2003/07/10 15:50:05 $
# Copyright: This module has been placed in the public domain.

"""
Writer module to integrate reST into Zope.  This writer subclasses the standard
html4css1 writer and changes the starting level for <H> elements from 1 to 3
(default behaviour inside Zope.
"""

__docformat__ = 'reStructuredText'

from docutils import nodes
from html4css1 import Writer  as CSS1Writer, HTMLTranslator as CSS1HTMLTranslator
import os

default_level = int(os.environ.get('STX_DEFAULT_LEVEL', 3))

class Writer(CSS1Writer):
    def __init__(self):
        CSS1Writer.__init__(self)
        self.translator_class = HTMLTranslator

class HTMLTranslator(CSS1HTMLTranslator):

    def astext(self):
        return ''.join(self.body)

    def visit_title(self, node):
        """Only 6 section levels are supported by HTML."""

        if isinstance(node.parent, nodes.topic):
            self.body.append(
                  self.starttag(node, 'p', '', CLASS='topic-title'))
            if node.parent.hasattr('id'):
                self.body.append(
                    self.starttag({}, 'a', '', name=node.parent['id']))
                self.context.append('</a></p>\n')
            else:
                self.context.append('</p>\n')
        elif self.section_level == 0:
            # document title
            self.head.append('<title>%s</title>\n'
                             % self.encode(node.astext()))
            self.body.append(self.starttag(node, 'h%d' % default_level, '', CLASS='title'))
            self.context.append('</h%d>\n' % default_level)
        else:
            self.body.append(
                  self.starttag(node, 'h%s' % (default_level+self.section_level-1), ''))
            atts = {}
            if node.parent.hasattr('id'):
                atts['name'] = node.parent['id']
            if node.hasattr('refid'):
                atts['class'] = 'toc-backref'
                atts['href'] = '#' + node['refid']
            self.body.append(self.starttag({}, 'a', '', **atts))
            self.context.append('</a></h%s>\n' % ((default_level+self.section_level-1)))
