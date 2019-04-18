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

import re

import six
from six import binary_type
from six import text_type

from DateTime import DateTime
from DateTime.interfaces import SyntaxError


try:
    from html import escape
except ImportError:  # PY2
    from cgi import escape

# This may get overwritten during configuration
default_encoding = 'utf-8'


def field2string(v):
    """Converts value to native strings.

    So always to `str` no matter which Python version you are on.
    """
    if hasattr(v, 'read'):
        return v.read()
    elif six.PY2 and isinstance(v, text_type):
        return v.encode(default_encoding)
    elif six.PY3 and isinstance(v, binary_type):
        return v.decode(default_encoding)
    else:
        return str(v)


def field2bytes(v):
    # Converts value to bytes.
    if hasattr(v, 'read'):
        return v.read()
    elif isinstance(v, text_type):
        return v.encode(default_encoding)
    else:
        return bytes(v)


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
                "An integer was expected in the value %r" % escape(
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
                escape(v, True)
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
                "A long integer was expected in the value %r" % escape(v, True)
            )
    raise ValueError('Empty entry when <strong>integer</strong> expected')


def field2tokens(v):
    v = field2string(v)
    return v.split()


def field2lines(v):
    if isinstance(v, (list, tuple)):
        result = []
        for item in v:
            result.append(field2bytes(item))
        return result
    return field2bytes(v).splitlines()


def field2date(v):
    v = field2string(v)
    try:
        v = DateTime(v)
    except SyntaxError:
        raise SyntaxError("Invalid DateTime " + escape(repr(v), True))
    return v


def field2date_international(v):
    v = field2string(v)
    try:
        v = DateTime(v, datefmt="international")
    except SyntaxError:
        raise SyntaxError("Invalid DateTime " + escape(repr(v)))
    return v


def field2boolean(v):
    if v == 'False':
        return False
    return bool(v)


class _unicode_converter(object):

    def __call__(self, v):
        # Convert a regular python string. This probably doesn't do
        # what you want, whatever that might be. If you are getting
        # exceptions below, you probably missed the encoding tag
        # from a form field name. Use:
        #       <input name="description:utf8:ustring" .....
        # rather than
        #       <input name="description:ustring" .....
        if hasattr(v, 'read'):
            v = v.read()
        v = text_type(v)
        return self.convert_unicode(v)

    def convert_unicode(self, v):
        raise NotImplementedError('convert_unicode')


class field2ustring(_unicode_converter):
    def convert_unicode(self, v):
        return v


field2ustring = field2ustring()


class field2utokens(_unicode_converter):
    def convert_unicode(self, v):
        return v.split()


field2utokens = field2utokens()


class field2utext(_unicode_converter):
    def convert_unicode(self, v):
        if isinstance(v, binary_type):
            return text_type(field2text(v.encode('utf8')), 'utf8')
        return v


field2utext = field2utext()


class field2ulines(object):
    def __call__(self, v):
        if hasattr(v, 'read'):
            v = v.read()
        if isinstance(v, (list, tuple)):
            return [field2ustring(x) for x in v]
        v = text_type(v)
        return self.convert_unicode(v)

    def convert_unicode(self, v):
        return field2utext.convert_unicode(v).splitlines()


field2ulines = field2ulines()


type_converters = {
    'float': field2float,
    'int': field2int,
    'long': field2long,
    'string': field2string,  # to native str
    'bytes': field2bytes,
    'date': field2date,
    'date_international': field2date_international,
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
