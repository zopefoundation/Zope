# -*- coding: iso-8859-1 -*-
# Author: Engelbert Gruber
# Contact: grubert@users.sourceforge.net
# Revision: $Revision: 1.2.10.3.8.1 $
# Date: $Date: 2004/05/12 19:57:50 $
# Copyright: This module has been placed in the public domain.

# New language mappings are welcome.  Before doing a new translation, please
# read <http://docutils.sf.net/spec/howto/i18n.html>.  Two files must be
# translated for each language: one in docutils/languages, the other in
# docutils/parsers/rst/languages.

"""
German-language mappings for language-dependent features of
reStructuredText.
"""

__docformat__ = 'reStructuredText'


directives = {
      'achtung': 'attention',
      'vorsicht': 'caution',
      'gefahr': 'danger',
      'fehler': 'error',
      'hinweis': 'hint',
      'wichtig': 'important',
      'notiz': 'note',
      'tip': 'tip',
      'warnung': 'warning',
      'ermahnung': 'admonition',
      'kasten': 'sidebar', # seitenkasten ?
      'thema': 'topic', 
      'line-block': 'line-block',
      'parsed-literal': 'parsed-literal',
      'rubrik': 'rubric',
      'epigraph (translation required)': 'epigraph',
      'highlights (translation required)': 'highlights',
      'pull-quote (translation required)': 'pull-quote', # kasten too ?
      'table (translation required)': 'table',
      #'questions': 'questions',
      #'qa': 'questions',
      #'faq': 'questions',
      'meta': 'meta',
      #'imagemap': 'imagemap',
      'bild': 'image',
      'abbildung': 'figure',
      'raw': 'raw',         # unbearbeitet
      'include': 'include', # einfügen, "füge ein" would be more like a command.
                            # einfügung would be the noun. 
      'ersetzung': 'replace', # ersetzen, ersetze
      'unicode': 'unicode',
      'klasse': 'class',    # offer "class" too ?
      'role (translation required)': 'role',
      'inhalt': 'contents',
      'sectnum': 'sectnum',
      'section-numbering': 'sectnum',
      'target-notes': 'target-notes',
      #'footnotes': 'footnotes',
      #'citations': 'citations',
      'restructuredtext-test-directive': 'restructuredtext-test-directive'}
"""German name to registered (in directives/__init__.py) directive name
mapping."""

roles = {
      'abbreviation (translation required)': 'abbreviation',
      'acronym (translation required)': 'acronym',
      'index (translation required)': 'index',
      'subscript (translation required)': 'subscript',
      'superscript (translation required)': 'superscript',
      'title-reference (translation required)': 'title-reference',
      'pep-reference (translation required)': 'pep-reference',
      'rfc-reference (translation required)': 'rfc-reference',
      'emphasis (translation required)': 'emphasis',
      'strong (translation required)': 'strong',
      'literal (translation required)': 'literal',
      'named-reference (translation required)': 'named-reference',
      'anonymous-reference (translation required)': 'anonymous-reference',
      'footnote-reference (translation required)': 'footnote-reference',
      'citation-reference (translation required)': 'citation-reference',
      'substitution-reference (translation required)': 'substitution-reference',
      'target (translation required)': 'target',
      'uri-reference (translation required)': 'uri-reference',}
"""Mapping of German role names to canonical role names for interpreted text.
"""
