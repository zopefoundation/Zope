import new

def copy_code_with_changes(codeobject,
                           argcount=None,
                           nlocals=None,
                           stacksize=None,
                           flags=None,
                           code=None,
                           consts=None,
                           names=None,
                           varnames=None,
                           filename=None,
                           name=None,
                           firstlineno=None,
                           lnotab=None):
    if argcount    is None: argcount    = codeobject.co_argcount
    if nlocals     is None: nlocals     = codeobject.co_nlocals
    if stacksize   is None: stacksize   = codeobject.co_stacksize
    if flags       is None: flags       = codeobject.co_flags
    if code        is None: code        = codeobject.co_code
    if consts      is None: consts      = codeobject.co_consts
    if names       is None: names       = codeobject.co_names
    if varnames    is None: varnames    = codeobject.co_varnames
    if filename    is None: filename    = codeobject.co_filename
    if name        is None: name        = codeobject.co_name
    if firstlineno is None: firstlineno = codeobject.co_firstlineno
    if lnotab      is None: lnotab      = codeobject.co_lnotab
    return new.code(argcount,
                    nlocals,
                    stacksize,
                    flags,
                    code,
                    consts,
                    names,
                    varnames,
                    filename,
                    name,
                    firstlineno,
                    lnotab)

code_attrs=['argcount',
            'nlocals',
            'stacksize',
            'flags',
            'code',
            'consts',
            'names',
            'varnames',
            'filename',
            'name',
            'firstlineno',
            'lnotab']


