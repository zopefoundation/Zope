import string

""" Pretty-Print an Interface object as structured text (Yum) """


def trim_doc_string(text):
    """
    Trims a doc string to make it format
    correctly with structured text.
    """
    text=string.strip(text)
    text=string.replace(text, '\r\n', '\n')
    lines=string.split(text, '\n')
    nlines=[lines[0]]
    if len(lines) > 1:
        min_indent=None
        for line in lines[1:]:
            indent=len(line) - len(string.lstrip(line))
            if indent < min_indent or min_indent is None:
                min_indent=indent   
        for line in lines[1:]:
            nlines.append(line[min_indent:])
    return string.join(nlines, '\n')
    
    
    
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



    



