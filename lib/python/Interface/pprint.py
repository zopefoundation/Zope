import string

""" Pretty-Print an Interface object as structured text (Yum) """

def justify_and_indent(text, level, munge=0, width=72):
    """ strip newlines, indent and justify text """

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
            

def build_signature(meth):
    """ this is a lot of work just to build a signature... """
    sig = "("
    for v in meth.positional:
        sig = sig + v
        if v in meth.optional.keys():
            sig = sig + "=%s" % `meth.optional[v]`
        sig = sig + ", "
    if meth.varargs:
        sig = sig + "*args, "
    if meth.kwargs:
        sig = sig + "**kws, "

    # slice off the last comma and space
    if meth.positional or meth.varargs or meth.kwargs:
        sig = sig[:-2]
        
    sig = sig + ")"
    return sig

def interface_as_stx(I, munge=0):
    """ Output structured text format.  Note, this will wack any existing
    'structured' format of the text.  """

    outp = "%s\n\n" % I.__name__
    level = 1

    if I.__doc__:
        outp = outp + justify_and_indent(I.__doc__, level) + "\n\n"

    if I.__bases__:
        outp = outp + (" " * level) + "This interface extends:\n\n"
        level = level + 1
        for b in I.__bases__:
            item = "o %s" % b.__name__
            outp = outp + justify_and_indent(item, level, munge) + "\n\n"
        level = level - 1

    level = level + 1
    for name, desc in I.namesAndDescriptions():
        item = "%s%s -- %s" % (name, build_signature(desc), desc.__doc__)
        outp = outp + justify_and_indent(item, level, munge)  + "\n\n"

    return outp



    



