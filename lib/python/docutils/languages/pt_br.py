# -*- coding: iso-8859-1 -*-
# Author: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.1.2.1 $
# Date: $Date: 2004/05/12 19:57:42 $
# Copyright: This module has been placed in the public domain.

# New language mappings are welcome.  Before doing a new translation, please
# read <http://docutils.sf.net/spec/howto/i18n.html>.  Two files must be
# translated for each language: one in docutils/languages, the other in
# docutils/parsers/rst/languages.

"""
Brazilian Portuguese-language mappings for language-dependent features of Docutils.
"""

__docformat__ = 'reStructuredText'

labels = {
      # fixed: language-dependent
      'author': u'Autor',
      'authors': u'Autores',
      'organization': unicode('Organização', 'latin1'),
      'address': unicode('Endereço', 'latin1'),
      'contact': u'Contato',
      'version': unicode('Versão', 'latin1'),
      'revision': unicode('Revisão', 'latin1'),
      'status': u'Estado',
      'date': u'Data',
      'copyright': u'Copyright',
      'dedication': unicode('Dedicatória', 'latin1'),
      'abstract': u'Resumo',
      'attention': unicode('Attenção!', 'latin1'),
      'caution': u'Cuidado!',
      'danger': u'PERIGO!',
      'error': u'Erro',
      'hint': unicode('Sugestão', 'latin1'),
      'important': u'Importante',
      'note': u'Nota',
      'tip': u'Dica',
      'warning': u'Aviso',
      'contents': unicode('Sumário', 'latin1')}
"""Mapping of node class name to label text."""

bibliographic_fields = {
      # language-dependent: fixed
      u'autor': 'author',
      u'autores': 'authors',
      unicode('organização', 'latin1'): 'organization',
      unicode('endereço', 'latin1'): 'address',
      u'contato': 'contact',
      unicode('versão', 'latin1'): 'version',
      unicode('revisão', 'latin1'): 'revision',
      u'estado': 'status',
      u'data': 'date',
      u'copyright': 'copyright',
      unicode('dedicatória', 'latin1'): 'dedication',
      u'resumo': 'abstract'}
"""English (lowcased) to canonical name mapping for bibliographic fields."""

author_separators = [';', ',']
"""List of separator strings for the 'Authors' bibliographic field. Tried in
order."""
