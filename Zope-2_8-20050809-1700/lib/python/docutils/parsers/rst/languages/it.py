# Author: Nicola Larosa, Lele Gaifax
# Contact: docutils@tekNico.net, lele@seldati.it
# Revision: $Revision: 1.2.10.7 $
# Date: $Date: 2005/01/07 13:26:04 $
# Copyright: This module has been placed in the public domain.

# New language mappings are welcome.  Before doing a new translation, please
# read <http://docutils.sf.net/docs/howto/i18n.html>.  Two files must be
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
      'ammonizione': 'admonition',
      'riquadro': 'sidebar',
      'argomento': 'topic',
      'blocco-di-righe': 'line-block',
      'blocco-interpretato': 'parsed-literal',
      'rubrica': 'rubric',
      'epigrafe': 'epigraph',
      'evidenzia': 'highlights',
      'pull-quote (translation required)': 'pull-quote',
      'compound (translation required)': 'compound',
      #'questions': 'questions',
      #'qa': 'questions',
      #'faq': 'questions',
      'tabella': 'table',
      'csv-table (translation required)': 'csv-table',
      'meta': 'meta',
      #'imagemap': 'imagemap',
      'immagine': 'image',
      'figura': 'figure',
      'includi': 'include',
      'grezzo': 'raw',
      'sostituisci': 'replace',
      'unicode': 'unicode',
      'classe': 'class',
      'ruolo': 'role',
      'indice': 'contents',
      'seznum': 'sectnum',
      'sezioni-autonumerate': 'sectnum',
      'annota-riferimenti-esterni': 'target-notes',
      #'footnotes': 'footnotes',
      #'citations': 'citations',
      'restructuredtext-test-directive': 'restructuredtext-test-directive'}
"""Italian name to registered (in directives/__init__.py) directive name
mapping."""

roles = {
      'abbreviazione': 'abbreviation',
      'acronimo': 'acronym',
      'indice': 'index',
      'deponente': 'subscript',
      'esponente': 'superscript',
      'riferimento-titolo': 'title-reference',
      'riferimento-pep': 'pep-reference',
      'riferimento-rfc': 'rfc-reference',
      'enfasi': 'emphasis',
      'forte': 'strong',
      'letterale': 'literal',
      'riferimento-con-nome': 'named-reference',
      'riferimento-anonimo': 'anonymous-reference',
      'riferimento-nota': 'footnote-reference',
      'riferimento-citazione': 'citation-reference',
      'riferimento-sostituzione': 'substitution-reference',
      'destinazione': 'target',
      'riferimento-uri': 'uri-reference',
      'grezzo': 'raw',}
"""Mapping of Italian role names to canonical role names for interpreted text.
"""
