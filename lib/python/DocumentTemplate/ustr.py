from types import StringType, UnicodeType, InstanceType

nasty_exception_str = Exception.__str__.im_func

def ustr(v):
    """convert an object to a plain string or unicode string
    """
    string_types = (StringType,UnicodeType)
    if type(v) in string_types:
        return v
    else:
        fn = getattr(v,'__str__',None)
        if fn is not None:
            # An object that wants to present its own string representation,
            # but we dont know what type of string. We cant use any built-in
            # function like str() or unicode() to retrieve it because
            # they all constrain the type which potentially raises an exception.
            # To avoid exceptions we have to call __str__ direct.
            if getattr(fn,'im_func',None)==nasty_exception_str:
                # Exception objects have been optimised into C, and their
                # __str__ function fails when given a unicode object.
                # Unfortunately this scenario is all too common when
                # migrating to unicode, because of code which does:
                # raise ValueError(something_I_wasnt_expecting_to_be_unicode)
                return _exception_str(v)
            else:
                # Trust the object to do this right
                v = fn()
                if type(v) in string_types:
                    return v
                else:
                    raise ValueError('__str__ returned wrong type')
        # Drop through for non-instance types, and instances that
        # do not define a special __str__
        return str(v)


def _exception_str(self):
    if not self.args:
        return ''
    elif len(self.args) == 1:
        return ustr(self.args[0])
    else:
        return str(self.args)
