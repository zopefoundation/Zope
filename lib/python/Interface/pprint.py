import string

""" Pretty-Print an Interface object as structured text (Yum) """


def justify_and_indent(text, level, munge=0, width=72):
    """ indent and justify text, rejustify (munge) if specified """

    lines = []

    if munge:
        line = " " * level
        text = string.split(string.strip(string.translate(text, string.maketrans("\r\n", "  "))))

        for word in text:
            line = string.join([line, word])
            if len(line) > width:
                lines.append(line)
                line = " " * level
        else:
            lines.append(line)

        return string.join(lines, "\n")

    else:
        text = string.split(string.replace(text,"\r\n", "\n"), "\n")

        for line in text:
            lines.append( (" " * level) + line)

        return string.join(lines, "\n")
            

def interface_as_stx(I, munge=0):
    """ Output structured text format.  Note, this will wack any existing
    'structured' format of the text.  """

    outp = "%s\n\n" % I.getName()
    level = 1

    if I.getDoc():
        outp = outp + justify_and_indent(I.getDoc(), level) + "\n\n"

    if I.getBases():
        outp = outp + (" " * level) + "This interface extends:\n\n"
        level = level + 1
        for b in I.getBases():
            item = "o %s" % b.getName()
            outp = outp + justify_and_indent(item, level, munge) + "\n\n"
        level = level - 1

    level = level + 1
    for name, desc in I.namesAndDescriptions():
        if hasattr(desc, 'getSignatureRepr'):   # ugh...
            item = "%s%s -- %s" % (desc.getName(), desc.getSignatureRepr(), desc.getDoc())
        else:
            item = "%s -- %s" % (desc.getName(), desc.getDoc())
            
        outp = outp + justify_and_indent(item, level, munge)  + "\n\n"

    return outp



    



