""" Pretty-Print an Interface object as structured text (Yum) """

import string

def trim_doc_string(text):
    """
    Trims a doc string to make it format
    correctly with structured text.
    """
    text=text.strip()
    text=text.replace('\r\n', '\n')
    lines=text.split('\n')
    nlines=[lines[0]]
    if len(lines) > 1:
        min_indent=None
        for line in lines[1:]:
            indent=len(line) - len(line.lstrip())
            if indent < min_indent or min_indent is None:
                min_indent=indent
        for line in lines[1:]:
            nlines.append(line[min_indent:])
    return '\n'.join(nlines)



def justify_and_indent(text, level, munge=0, width=72):
    """ indent and justify text, rejustify (munge) if specified """

    lines = []

    if munge:
        line = " " * level
        text = (string.translate(text, string.maketrans("\r\n", "  "))).strip.split()

        for word in text:
            line = ''.join([line, word])
            if len(line) > width:
                lines.append(line)
                line = " " * level
        else:
            lines.append(line)

        return '\n'.join(lines)

    else:
        text = text.replace("\r\n", "\n").split( "\n")

        for line in text:
            lines.append( (" " * level) + line)

        return '\n'.join(lines)


def interface_as_stx(I, munge=0):
    """ Output structured text format.  Note, this will wack any existing
    'structured' format of the text.  """

    outp = "%s\n\n" % I.getName()
    level = 1

    if I.getDoc():
        outp = outp + justify_and_indent(trim_doc_string(I.getDoc()), level) + "\n\n"

    if I.getBases():
        outp = outp + (" " * level) + "This interface extends:\n\n"
        level = level + 1
        for b in I.getBases():
            item = "o %s" % b.getName()
            outp = outp + justify_and_indent(trim_doc_string(item), level, munge) + "\n\n"
        level = level - 1

    level = level + 1
    for name, desc in I.namesAndDescriptions():
        if hasattr(desc, 'getSignatureRepr'):   # ugh...
            item = "%s%s -- %s" % (desc.getName(), desc.getSignatureRepr(), desc.getDoc())
        else:
            item = "%s -- %s" % (desc.getName(), desc.getDoc())

        outp = outp + justify_and_indent(trim_doc_string(item), level, munge)  + "\n\n"

    return outp
