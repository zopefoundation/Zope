# Author: Marek Blaha
# Contact: mb@dat.cz
# Revision: $Revision: 1.1.2.1 $
# Date: $Date: 2004/05/12 19:57:50 $
# Copyright: This module has been placed in the public domain.

# New language mappings are welcome.  Before doing a new translation, please
# read <http://docutils.sf.net/spec/howto/i18n.html>.  Two files must be
# translated for each language: one in docutils/languages, the other in
# docutils/parsers/rst/languages.

"""
Czech-language mappings for language-dependent features of
reStructuredText.
"""

__docformat__ = 'reStructuredText'


directives = {
      # language-dependent: fixed
      u'pozor': 'attention',
      u'caution': 'caution',       # jak rozlisit caution a warning?
      u'nebezpe\u010D\u00ED': 'danger',
      u'chyba': 'error',
      u'rada': 'hint',
      u'd\u016Fle\u017Eit\u00E9': 'important',
      u'pozn\u00E1mka': 'note',
      u'tip': 'tip',
      u'varov\u00E1n\u00ED': 'warning',
      u'admonition': 'admonition',
      u'sidebar': 'sidebar',
      u't\u00E9ma': 'topic',
      u'line-block': 'line-block',
      u'parsed-literal': 'parsed-literal',
      u'odd\u00EDl': 'rubric',
      u'moto': 'epigraph',
      u'highlights': 'highlights',
      u'pull-quote': 'pull-quote',
      #'questions': 'questions',
      #'qa': 'questions',
      #'faq': 'questions',
      u'table (translation required)': 'table',
      u'csv-table (translation required)': 'csv-table',
      u'meta': 'meta',
      #'imagemap': 'imagemap',
      u'image': 'image',   # obrazek
      u'figure': 'figure', # a tady?
      u'include': 'include',
      u'raw': 'raw',
      u'replace': 'replace',
      u'unicode': 'unicode',
      u't\u0159\u00EDda': 'class',
      u'role (translation required)': 'role',
      u'obsah': 'contents',
      u'sectnum': 'sectnum',
      u'section-numbering': 'sectnum',
      #'footnotes': 'footnotes',
      #'citations': 'citations',
      u'target-notes': 'target-notes',
      u'restructuredtext-test-directive': 'restructuredtext-test-directive'}
"""Czech name to registered (in directives/__init__.py) directive name
mapping."""

roles = {
    # language-dependent: fixed
    u'abbreviation': 'abbreviation',
    u'ab': 'abbreviation',
    u'acronym': 'acronym',
    u'ac': 'acronym',
    u'index': 'index',
    u'i': 'index',
    u'subscript': 'subscript',
    u'sub': 'subscript',
    u'superscript': 'superscript',
    u'sup': 'superscript',
    u'title-reference': 'title-reference',
    u'title': 'title-reference',
    u't': 'title-reference',
    u'pep-reference': 'pep-reference',
    u'pep': 'pep-reference',
    u'rfc-reference': 'rfc-reference',
    u'rfc': 'rfc-reference',
    u'emphasis': 'emphasis',
    u'strong': 'strong',
    u'literal': 'literal',
    u'named-reference': 'named-reference',
    u'anonymous-reference': 'anonymous-reference',
    u'footnote-reference': 'footnote-reference',
    u'citation-reference': 'citation-reference',
    u'substitution-reference': 'substitution-reference',
    u'target': 'target',
    u'uri-reference': 'uri-reference',
    u'uri': 'uri-reference',
    u'url': 'uri-reference',}
"""Mapping of Czech role names to canonical role names for interpreted text.
"""
