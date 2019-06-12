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

used (mainly) by ``.request_parameters`` and ``OFS.PropertyManager``.


Backward incompatibilities
==========================

The converters no longer support file like input (because
we have no way to determine which encoding they use).


Important note about ``bytes`` as data type and converter
=========================================================

Python 2
--------

Under Python 2, ``bytes`` is a synonym for ``str`` and
a ``bytes`` value can both represent a intrinsic sequence of bytes
as well as an encoded text.

Under Python 2, there is no real need for a ``bytes`` converter
(and in fact, Zope introduced it only once it started to support Python 3).

Python 3
--------

Under Python 3, a ``bytes`` value typically represents an
intrinsic sequence of bytes; such a sequence may represent
an encoded text but this is rare (and mainly used only at system
boundaries).

An intrinsic sequence of bytes is often represented as
text via "latin-1" decoding. This maps byte *b* to unicode codepoint *b*.

Interpretation of ``bytes``
---------------------------

The converters below interpret a binary value (i.e. a ``bytes``
value under Python 3) as an intrinsic sequence of bytes without
an implicit relation to text.

If a converter converts between a binary value and a text value,
then the "latin-1" encoding (and not the ``default_encoding``) is used
by default. The converter can be called with an explicit *encoding*
parameter to change this.

The ``bytes`` converter is interpreted to produce a binary value
and therefore, by default uses the "latin-1" encoding.
"""

import re

import six
from six import binary_type
from six import raise_from
from six import text_type

from DateTime import DateTime
from DateTime.interfaces import SyntaxError


try:
    from html import escape
except ImportError:  # PY2
    from cgi import escape

# This may get overwritten during configuration
default_encoding = 'utf-8'


class Converter(object):
    """Base class.

    It converts to "native string".
    """
    input_types = object,

    def __call__(self, v, encoding=None):
        if six.PY2 and isinstance(v, text_type):
            return v.encode(encoding or default_encoding)
        if six.PY3 and isinstance(v, binary_type):
            # see note in module docstring
            return v.decode(encoding or "latin-1")
        return str(v)


if six.PY3:
    UConverter = Converter
else:
    class UConverter(Converter):
        """converts to unicode (aka ``text_type``)."""
        def __call__(self, v, encoding=None):
            if isinstance(v, str):
                return v.decode(encoding or default_encoding)
            return unicode(v)  # noqa: F821


field2string = Converter()
field2ustring = UConverter()


class BytesConverter(Converter):
    """convert to a binary value.

    See note in module docstring.
    """
    input_types = bytes, str, text_type

    def __call__(self, v, encoding=None):
        if isinstance(v, text_type):
            return v.encode(encoding or "latin1")
        return bytes(v)


field2bytes = BytesConverter()


class TypeSequenceConverter(Converter):
    """convert to *output_type*.

    If *v* is a ``list`` or ``tuple``, the converter
    is recursively applied to its elements.
    Note: This feature likely comes from a misunderstanding of the
    request parameter converter documentation and is likely not used.
    """
    def __init__(self, output_type, clean=None):
        self.output_type = output_type
        self.clean = clean

    def __call__(self, v, encoding=None):
        if isinstance(v, (list, tuple)):
            return v.__class__(self(x, encoding) for x in v)
        t = self.output_type
        if isinstance(v, t):
            return v
        v = super(TypeSequenceConverter, self).__call__(v, encoding)
        if self.clean:
            v = self.clean(v)
        try:
            return t(v)
        except (ValueError, TypeError) as e:
            raise_from(ValueError("Expected %s in value %r"
                                  % (t.__name__,
                                     escape(v, quote=True))),
                       e)


class TransformerMixin(object):
    """converts by regular expression transformation."""
    def __init__(self, transform):
        self.transform = transform

    def __call__(self, v, encoding=None):
        v = super(TransformerMixin, self).__call__(v, encoding)
        return self.transform(v)


class Transformer(TransformerMixin, Converter):
    pass


class UTransformer(TransformerMixin, UConverter):
    pass


lineend = re.compile("[\r\n]{1,2}", re.M)
text_transform = lambda v, sub=lineend.sub: sub("\n", v)  # noqa: E731
field2text = Transformer(text_transform)
field2utext = UTransformer(text_transform)


def field2required(v):
    v = field2string(v)
    if v.strip():
        return v
    raise ValueError('No input for required field<p>')


if six.PY3:
    long = int

field2int = TypeSequenceConverter(int)
field2float = TypeSequenceConverter(float)
field2long = TypeSequenceConverter(
    long,
    lambda v: v if not (v.endswith("l") or v.endswith("L")) else v[:-1])


class SplitterMixin(object):
    def __init__(self, split, keep_types=()):
        self.split = split
        self.keep_types = keep_types

    def __call__(self, v, encoding=None):
        if isinstance(v, self.keep_types):
            return v
        v = super(SplitterMixin, self).__call__(v, encoding)
        return [] if not v else self.split(v)


class Splitter(SplitterMixin, Converter):
    pass


class USplitter(SplitterMixin, UConverter):
    pass


token_split = re.compile(r"\s+").split
field2tokens = Splitter(token_split)
field2utokens = USplitter(token_split)
line_split = lineend.split
line_keep = (list, tuple)
field2lines = Splitter(line_split, line_keep)
field2ulines = USplitter(line_split, line_keep)


class DateConverter(Converter):
    def __init__(self, **kw):
        self.kw = kw

    def __call__(self, v, encoding=None):
        v = super(DateConverter, self).__call__(v, encoding)
        try:
            return DateTime(v, **self.kw)
        except SyntaxError as e:
            raise_from(ValueError("Invalid Datetime" + escape(repr(v), True)),
                       e)


field2date = DateConverter()
field2date_international = DateConverter(datefmt="international")


def field2boolean(v):
    if v == 'False':
        return False
    return bool(v)


def field2none(v):
    return


field2none.input_types = object,


type_converters = {
    'float': field2float,
    'int': field2int,
    'long': field2long,
    'string': field2string,  # to native str
    'bytes': field2bytes,  # to binary value
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
    'none': field2none,  # None
}

get_converter = type_converters.get
