# Author: Nicola Larosa
# Contact: docutils@tekNico.net
# Revision: $Revision: 1.3 $
# Date: $Date: 2003/07/10 15:49:49 $
# Copyright: This module has been placed in the public domain.

# New language mappings are welcome.  Before doing a new translation, please
# read <http://docutils.sf.net/spec/howto/i18n.html>.  Two files must be
# translated for each language: one in docutils/languages, the other in
# docutils/parsers/rst/languages.

"""
Italian-language mappings for language-dependent features of
reStructuredText.
"""

__docformat__ = 'reStructuredText'


directives = {
      'attenzione': 'attention',
      'cautela': 'caution',
      'pericolo': 'danger',
      'errore': 'error',
      'suggerimento': 'hint',
      'importante': 'important',
      'nota': 'note',
      'consiglio': 'tip',
      'avvertenza': 'warning',
      'admonition (translation required)': 'admonition',
      'sidebar (translation required)': 'sidebar',
      'argomento': 'topic',
      'blocco di linee': 'line-block',
      'parsed-literal': 'parsed-literal',
      'rubric (translation required)': 'rubric',
      'epigraph (translation required)': 'epigraph',
      'highlights (translation required)': 'highlights',
      'pull-quote (translation required)': 'pull-quote',
      #'questions': 'questions',
      #'qa': 'questions',
      #'faq': 'questions',
      'meta': 'meta',
      #'imagemap': 'imagemap',
      'immagine': 'image',
      'figura': 'figure',
      'includi': 'include',
      'grezzo': 'raw',
      'sostituisci': 'replace',
      'unicode': 'unicode',
      'class (translation required)': 'class',
      'indice': 'contents',
      'seznum': 'sectnum',
      'section-numbering': 'sectnum',
      'target-notes': 'target-notes',
      #'footnotes': 'footnotes',
      #'citations': 'citations',
      'restructuredtext-test-directive': 'restructuredtext-test-directive'}
"""Italian name to registered (in directives/__init__.py) directive name
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
"""Mapping of Italian role names to canonical role names for interpreted text.
"""
