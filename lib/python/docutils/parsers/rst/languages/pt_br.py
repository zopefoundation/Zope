# -*- coding: iso-8859-1 -*-
# Author: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.1.2.1 $
# Date: $Date: 2004/05/12 19:57:51 $
# Copyright: This module has been placed in the public domain.

# New language mappings are welcome.  Before doing a new translation, please
# read <http://docutils.sf.net/spec/howto/i18n.html>.  Two files must be
# translated for each language: one in docutils/languages, the other in
# docutils/parsers/rst/languages.

"""
Brazilian Portuguese-language mappings for language-dependent features of
reStructuredText.
"""

__docformat__ = 'reStructuredText'


directives = {
      # language-dependent: fixed
      u'atenção': 'attention',
      'cuidado': 'caution',
      'perigo': 'danger',
      'erro': 'error',
      u'sugestão': 'hint',
      'importante': 'important',
      'nota': 'note',
      'dica': 'tip',
      'aviso': 'warning',
      u'exortação': 'admonition',
      'barra-lateral': 'sidebar',
      u'tópico': 'topic',
      'bloco-de-linhas': 'line-block',
      'literal-interpretado': 'parsed-literal',
      'rubrica': 'rubric',
      u'epígrafo': 'epigraph',
      'destaques': 'highlights',
      u'citação-destacada': 'pull-quote',
      u'table (translation required)': 'table',
      #'perguntas': 'questions',
      #'qa': 'questions',
      #'faq': 'questions',
      'meta': 'meta',
      #'imagemap': 'imagemap',
      'imagem': 'image',
      'figura': 'figure',
      u'inclusão': 'include',
      'cru': 'raw',
      u'substituição': 'replace',
      'unicode': 'unicode',
      'classe': 'class',
      'role (translation required)': 'role',
      u'índice': 'contents',
      'numsec': 'sectnum',
      u'numeração-de-seções': 'sectnum',
      #u'notas-de-rorapé': 'footnotes',
      #u'citações': 'citations',
      u'links-no-rodapé': 'target-notes',
      'restructuredtext-test-directive': 'restructuredtext-test-directive'}
"""English name to registered (in directives/__init__.py) directive name
mapping."""

roles = {
    # language-dependent: fixed
    u'abbreviação': 'abbreviation',
    'ab': 'abbreviation',
    u'acrônimo': 'acronym',
    'ac': 'acronym',
    u'índice-remissivo': 'index',
    'i': 'index',
    'subscrito': 'subscript',
    'sub': 'subscript',
    'sobrescrito': 'superscript',
    'sob': 'superscript',
    u'referência-a-título': 'title-reference',
    u'título': 'title-reference',
    't': 'title-reference',
    u'referência-a-pep': 'pep-reference',
    'pep': 'pep-reference',
    u'referência-a-rfc': 'rfc-reference',
    'rfc': 'rfc-reference',
    u'ênfase': 'emphasis',
    'forte': 'strong',
    'literal': 'literal',
    u'referência-por-nome': 'named-reference',
    u'referência-anônima': 'anonymous-reference',
    u'referência-a-nota-de-rodapé': 'footnote-reference',
    u'referência-a-citação': 'citation-reference',
    u'referência-a-substituição': 'substitution-reference',
    'alvo': 'target',
    u'referência-a-uri': 'uri-reference',
    'uri': 'uri-reference',
    'url': 'uri-reference',}
"""Mapping of English role names to canonical role names for interpreted text.
"""
