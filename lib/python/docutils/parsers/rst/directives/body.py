# Author: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.5 $
# Date: $Date: 2003/11/30 15:06:06 $
# Copyright: This module has been placed in the public domain.

"""
Directives for additional body elements.
"""

__docformat__ = 'reStructuredText'


import sys
from docutils import nodes
from docutils.parsers.rst import directives


def topic(name, arguments, options, content, lineno,
          content_offset, block_text, state, state_machine,
          node_class=nodes.topic):
    if not state_machine.match_titles:
        error = state_machine.reporter.error(
              'The "%s" directive may not be used within topics, sidebars, '
              'or body elements.' % name,
              nodes.literal_block(block_text, block_text), line=lineno)
        return [error]
    if not content:
        warning = state_machine.reporter.warning(
            'Content block expected for the "%s" directive; none found.'
            % name, nodes.literal_block(block_text, block_text),
            line=lineno)
        return [warning]
    title_text = arguments[0]
    textnodes, messages = state.inline_text(title_text, lineno)
    titles = [nodes.title(title_text, '', *textnodes)]
    if options.has_key('subtitle'):
        textnodes, more_messages = state.inline_text(options['subtitle'],
                                                     lineno)
        titles.append(nodes.subtitle(options['subtitle'], '', *textnodes))
        messages.extend(more_messages)
    text = '\n'.join(content)
    node = node_class(text, *(titles + messages))
    if options.has_key('class'):
        node.set_class(options['class'])
    if text:
        state.nested_parse(content, content_offset, node)
    return [node]

topic.arguments = (1, 0, 1)
topic.options = {'class': directives.class_option}
topic.content = 1

def sidebar(name, arguments, options, content, lineno,
            content_offset, block_text, state, state_machine):
    return topic(name, arguments, options, content, lineno,
                 content_offset, block_text, state, state_machine,
                 node_class=nodes.sidebar)

sidebar.arguments = (1, 0, 1)
sidebar.options = {'subtitle': directives.unchanged_required,
                   'class': directives.class_option}
sidebar.content = 1

def line_block(name, arguments, options, content, lineno,
               content_offset, block_text, state, state_machine,
               node_class=nodes.line_block):
    if not content:
        warning = state_machine.reporter.warning(
            'Content block expected for the "%s" directive; none found.'
            % name, nodes.literal_block(block_text, block_text), line=lineno)
        return [warning]
    text = '\n'.join(content)
    text_nodes, messages = state.inline_text(text, lineno)
    node = node_class(text, '', *text_nodes, **options)
    return [node] + messages

line_block.options = {'class': directives.class_option}
line_block.content = 1

def parsed_literal(name, arguments, options, content, lineno,
                   content_offset, block_text, state, state_machine):
    return line_block(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine,
                      node_class=nodes.literal_block)

parsed_literal.options = {'class': directives.class_option}
parsed_literal.content = 1

def rubric(name, arguments, options, content, lineno,
             content_offset, block_text, state, state_machine):
    rubric_text = arguments[0]
    textnodes, messages = state.inline_text(rubric_text, lineno)
    rubric = nodes.rubric(rubric_text, '', *textnodes, **options)
    return [rubric] + messages

rubric.arguments = (1, 0, 1)
rubric.options = {'class': directives.class_option}

def epigraph(name, arguments, options, content, lineno,
             content_offset, block_text, state, state_machine):
    block_quote, messages = state.block_quote(content, content_offset)
    block_quote.set_class('epigraph')
    return [block_quote] + messages

epigraph.content = 1

def highlights(name, arguments, options, content, lineno,
             content_offset, block_text, state, state_machine):
    block_quote, messages = state.block_quote(content, content_offset)
    block_quote.set_class('highlights')
    return [block_quote] + messages

highlights.content = 1

def pull_quote(name, arguments, options, content, lineno,
             content_offset, block_text, state, state_machine):
    block_quote, messages = state.block_quote(content, content_offset)
    block_quote.set_class('pull-quote')
    return [block_quote] + messages

pull_quote.content = 1
