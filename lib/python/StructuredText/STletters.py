import string

def punc_func(exclude):
    punc = r''
    for char in string.punctuation:
        if char not in exclude:
            punc = punc + r'\%s' % char
    return punc

digits      = string.digits
letters     = string.letters
literal_punc = punc_func("'")
dbl_quoted_punc = punc_func("\"")
strongem_punc = punc_func('*')
under_punc = punc_func('_<>')
phrase_delimiters = r'\s\.\,\?\/\!\&\(\)'
