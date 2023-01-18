##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""Converters

Used by `ZPublisher.HTTPRequest` and `OFS.PropertyManager`.

Binary converters (i.e. converters which use `bytes` for/in their result)
are marked with a true `binary` attribute`.
This allows the publisher to perform the conversion to `bytes`
based on its more precise encoding knowledge.
"""


import html
import json
import re
import warnings

from DateTime import DateTime
from DateTime.interfaces import SyntaxError


# This may get overwritten during configuration
default_encoding = 'utf-8'


def field2string(v):
    """Converts value to string."""
    if isinstance(v, bytes):
        return v.decode(default_encoding)
    else:
        return str(v)


def field2bytes(v):
    """Converts value to bytes."""
    if hasattr(v, 'read'):
        return v.read()
    elif isinstance(v, str):
        return v.encode(default_encoding)
    else:
        return bytes(v)


field2bytes.binary = True


def field2text(value, nl=re.compile('\r\n|\n\r').search):
    value = field2string(value)
    match_object = nl(value)
    if match_object is None:
        return value
    length = match_object.start(0)
    result = []
    start = 0
    while length >= start:
        result.append(value[start:length])
        start = length + 2
        match_object = nl(value, start)
        if match_object is None:
            length = -1
        else:
            length = match_object.start(0)

    result.append(value[start:])

    return '\n'.join(result)


def field2required(v):
    v = field2string(v)
    if v.strip():
        return v
    raise ValueError('No input for required field<p>')


def field2int(v):
    if isinstance(v, (list, tuple)):
        return list(map(field2int, v))
    v = field2string(v)
    if v:
        try:
            return int(v)
        except ValueError:
            raise ValueError(
                "An integer was expected in the value %r" % html.escape(
                    v, quote=True
                )
            )
    raise ValueError('Empty entry when <strong>integer</strong> expected')


def field2float(v):
    if isinstance(v, (list, tuple)):
        return list(map(field2float, v))
    v = field2string(v)
    if v:
        try:
            return float(v)
        except ValueError:
            raise ValueError(
                "A floating-point number was expected in the value %r" %
                html.escape(v, True)
            )
    raise ValueError(
        'Empty entry when <strong>floating-point number</strong> expected')


def field2long(v):
    if isinstance(v, (list, tuple)):
        return list(map(field2long, v))
    v = field2string(v)
    # handle trailing 'L' if present.
    if v[-1:] in ('L', 'l'):
        v = v[:-1]
    if v:
        try:
            return int(v)
        except ValueError:
            raise ValueError(
                "A long integer was expected in the value %r" %
                html.escape(
                    v, True))
    raise ValueError('Empty entry when <strong>integer</strong> expected')


def field2tokens(v):
    v = field2string(v)
    return v.split()


def field2lines(v):
    if isinstance(v, (list, tuple)):
        return [field2string(item) for item in v]
    return field2string(v).splitlines()


def field2date(v):
    v = field2string(v)
    try:
        v = DateTime(v)
    except SyntaxError:
        raise SyntaxError("Invalid DateTime " + html.escape(repr(v), True))
    return v


def field2date_international(v):
    v = field2string(v)
    try:
        v = DateTime(v, datefmt="international")
    except SyntaxError:
        raise SyntaxError("Invalid DateTime " + html.escape(repr(v)))
    return v


def field2boolean(v):
    if v == 'False':
        return False
    return bool(v)


def field2ustring(v):
    warnings.warn(
        "The converter `(field2)ustring` is deprecated "
        "and will be removed in Zope 6. "
        "Please use `(field2)string` instead.",
        DeprecationWarning)
    return field2string(v)


def field2utokens(v):
    warnings.warn(
        "The converter `(field2)utokens` is deprecated "
        "and will be removed in Zope 6. "
        "Please use `(field2)tokens` instead.",
        DeprecationWarning)
    return field2tokens(v)


def field2utext(v):
    warnings.warn(
        "The converter `(field2)utext` is deprecated "
        "and will be removed in Zope 6. "
        "Please use `(field2)text` instead.",
        DeprecationWarning)
    return field2text(v)


def field2ulines(v):
    warnings.warn(
        "The converter `(field2u)lines` is deprecated "
        "and will be removed in Zope 6. "
        "Please use `(field2)lines` instead.",
        DeprecationWarning)
    return field2lines(v)


def field2json(v):
    try:
        v = json.loads(v)
    except ValueError:
        raise ValueError("Invalid json " + html.escape(repr(v), True))
    return v


type_converters = {
    'float': field2float,
    'int': field2int,
    'long': field2long,
    'string': field2string,
    'bytes': field2bytes,
    'date': field2date,
    'date_international': field2date_international,
    'json': field2json,
    'required': field2required,
    'tokens': field2tokens,
    'lines': field2lines,
    'text': field2text,
    'boolean': field2boolean,
    'ustring': field2ustring,
    'utokens': field2utokens,
    'ulines': field2ulines,
    'utext': field2utext,
}

get_converter = type_converters.get
