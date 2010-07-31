##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

import string, math

def format(text, max_width=80, indent=0, trailing_lines_indent_more=0):
    text = string.expandtabs(string.replace(text, '\r', ''))
    lines = string.split(text, '\n')
    aggregate = []
    for line in lines:
        if len(line) <= max_width-1:
            # this line is short enough to output
            aggregate.append(line)
        else:
            lines = splitlongline(line, max_width)
            aggregate.extend(lines)
    out = []
    i = 0
    for line in aggregate:
        spaces = ' ' * indent
        if i != 0 and trailing_lines_indent_more:
            spaces = spaces + (' ' * trailing_lines_indent_more)
        out.append('%s%s' % (spaces, line))
        i = i + 1
    return string.join(out, '\n')

def splitword(word, max_width=80, linepos=0):
    # some lines may have single words that exceed the max_width
    # We want to break apart long words into as many chunks as necessary
    if len(word) <= max_width:
        return [word]
    first_chunk_len = max_width-1-linepos
    firstchunk = word[:first_chunk_len]
    word = word[first_chunk_len:]
    numchunks = int(math.ceil(len(word) / float(max_width-1)))
    index = 0
    tmp = [firstchunk]
    for chunknum in range(numchunks):
        chunk = word[index:index+max_width-1]
        tmp.append(chunk)
        index = index + max_width-1
    return tmp
    
def splitlongline(line, max_width=80):
    # split a "long" line defined by max_width into a list of lines
    line = string.strip(line)
    words = string.split(line, ' ')
    wordnum = 0
    # iterate over all the words in the line, extending the word list
    # necessary for too-long words
                
    aggregate = []
    linelen = 0
    wordnum = 0
    while words:
        word = words.pop(0)
        if not word: continue
        if len(word) > max_width:
            new_words = splitword(word, max_width, linelen)
            word = new_words[0]
            for new_word in new_words[1:]:
                words.insert(wordnum, new_word)
                wordnum = wordnum + 1
        if words:
            next_word = words[0]
        else:
            next_word = None
        if next_word is None:
            aggregate.append(word)
            wordnum = wordnum + 1
            continue
        maybe_len = linelen + len(word) + len(next_word)
        if maybe_len >= max_width-1:
            aggregate.append(word)
            aggregate.append(None)
            linelen = 0
        else:
            aggregate.append(word)
            linelen = linelen + len(word) + 1
        wordnum = wordnum + 1

    s = ""
    last = None
    for item in aggregate:
        if item is None:
            s = '%s\n' % s
        elif last is None:
            s = '%s%s' % (s, item)
        else:
            s = '%s %s' % (s, item)
        last = item
    return string.split(s, '\n')

long = """
To turn a component into a product you must fulfill many contracts. For the most part these contracts are not yet defined in terms of interfaces. Instead you must subclass from base classes that implement the contracts. This makes building products confusing, and this is an area that we are actively working on improving.  Hereisalonglinethatshouldbecaughtandbrokenupbytheformatter,hopefullyitllgetsplitupwhenirunitthroughthere."""
long2 = """
Hereisalonglinethatshouldbecaughtandbrokenupbytheformatter,hopefullyitllgetsplitupwhenirunitthroughthere."""
long3 = """
To turn a component into a product you must fulfill many contracts. For the most part these contracts are not yet defined in terms of interfaces.

Instead you must subclass from base classes that implement the contracts. This makes building products confusing, and this is an area that we are

actively working on improving.  Hereisalonglinethatshouldbecaughtandbrokenupbytheformatter,hopefullyitllgetsplitupwhenirunitthroughthere."""

if __name__ == '__main__':
    print format(long, 60, 10)
    print format(long)
    print format(long2, 60, 10)
    print format(long2)
    print format(long3, 60, 10)
    print format(long3)



