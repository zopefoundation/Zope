# Author: David Goodger, Dmitry Jemerov
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.2.10.6 $
# Date: $Date: 2005/01/07 13:26:04 $
# Copyright: This module has been placed in the public domain.

"""
Directives for document parts.
"""

__docformat__ = 'reStructuredText'

from docutils import nodes, languages
from docutils.transforms import parts
from docutils.parsers.rst import directives


backlinks_values = ('top', 'entry', 'none')

def backlinks(arg):
    value = directives.choice(arg, backlinks_values)
    if value == 'none':
        return None
    else:
        return value

def contents(name, arguments, options, content, lineno,
             content_offset, block_text, state, state_machine):
    """Table of contents."""
    document = state_machine.document
    language = languages.get_language(document.settings.language_code)

    if arguments:
        title_text = arguments[0]
        text_nodes, messages = state.inline_text(title_text, lineno)
        title = nodes.title(title_text, '', *text_nodes)
    else:
        messages = []
        if options.has_key('local'):
            title = None
        else:
            title = nodes.title('', language.labels['contents'])

    topic = nodes.topic(CLASS='contents')

    cls = options.get('class')
    if cls:
        topic.set_class(cls)

    if title:
        name = title.astext()
        topic += title
    else:
        name = language.labels['contents']

    name = nodes.fully_normalize_name(name)
    if not document.has_name(name):
        topic['name'] = name
    document.note_implicit_target(topic)

    pending = nodes.pending(parts.Contents, rawsource=block_text)
    pending.details.update(options)
    document.note_pending(pending)
    topic += pending
    return [topic] + messages

contents.arguments = (0, 1, 1)
contents.options = {'depth': directives.nonnegative_int,
                    'local': directives.flag,
                    'backlinks': backlinks,
                    'class': directives.class_option}

def sectnum(name, arguments, options, content, lineno,
            content_offset, block_text, state, state_machine):
    """Automatic section numbering."""
    pending = nodes.pending(parts.SectNum)
    pending.details.update(options)
    state_machine.document.note_pending(pending)
    return [pending]

sectnum.options = {'depth': int,
                   'start': int,
                   'prefix': directives.unchanged_required,
                   'suffix': directives.unchanged_required}
