"""Request parameter handling.

https://github.com/zopefoundation/Zope/issues/641 outlines the
aims of this implmentation.

We implement the following processing model:

1. The request parameters are fetched from the various sources
   (i.e. *query* and request body) and normalized in a way
   which does not assume a specific character encoding.
   The result is a sequence of *name*, *value* pairs,
   each describing a single request parameter.

2. We set up an empty form record and process earch request parameter
   in turn updating the form record.
   The form record will get flexible values (rather than pritimive ones)
   which support defaults, aggregation and convertion.

3. The form record is instantiated recursively converting its flexible
   value into a normal ``dict`` to be used as ``form``.

``.HTTPRequest.HTTPRequest.processInputs`` performs the
overall processing. ``process_parameters`` below implements
steps 2. and 3..

To implement the processing of a request parameter *name*, *value*
in step 2 above, *name* is parsed into a *key* and a sequence
of directives. A directive specifies either a converter,
a (character) encoding (typically for use with a converter) or
an aggregator. This implementation supports at most one converter
and one encoding. It uses *value* and *converter*/*encoding* (if any)
to form a `PrimaryValue`. The remaining sequence of aggregators
is executed from left to right where each aggregator can transform
the key and the value or stop the processing of this parameter as
a whole.

This module make use of three major classes:

Converter
    which implements the conversion of `str` to application specific types

    For backward compatibility reasons and because converters are
    also used by ``OFS.PropertyManager.PropertyManager``, the converters
    are defined in module ``.Converters``.

FlexValue
    which implements our flexible values

Aggregator
    which implements the aggregators as continuations operating on
    *key*, *value*, *further aggregators* tiples.
"""

from codecs import lookup
from re import compile
from six import PY3
from sys import exc_info

from .Converters import type_converters
from .HTTPRequest import FileUpload, record


class Markable(object):
    """Marks support for different types of marks."""

    _MARK_MAP = {}  # maps supported types to supported values

    # define ``dict`` ``MARK_TYPES`` in derived classes to extend ``_MARK_MAP``

    def __init__(self, *unused_args, **unused_kw):
        self.__marks = dict.fromkeys(self._MARK_MAP, "")

    def get_mark(self, type):
        return self.__marks[type]

    def mark(self, type, mark):
        if type not in self._MARK_MAP:
            raise TypeError("`%s` not supported for %s" %
                            (mark, self.__class__.__name__))
        if mark not in self._MARK_MAP[type]:  # noqa:
            raise NotImplementedError("illegal mark value `%s`" % mark)
        marks = self.__marks
        old_mark = marks[type]
        if old_mark:
            raise ValueError("Cannot %s mark `%s`; it is already marked %`s`"
                             % (type, mark, old_mark))
        marks[type] = mark

    @classmethod
    def __init_subclass__(cls):
        if "MARK_TYPES" in cls.__dict__:
            m = cls._MARK_MAP = cls._MARK_MAP.copy()
            m.update(cls.MARK_TYPES)


class FlexValue(Markable):
    """Base class to implement "flexible" values.

    A "flexible" value supports defaults, update and aggregation.

    A "flexible" value is a wrapper for a "wrapped" value.
    """

    MARK_TYPES = {"usage": ("default", "conditional", "replace")}

    def __init__(self, wrapped):
        super(FlexValue, self).__init__(self)
        self.wrapped = wrapped

    def instantiate(self, errors=None):
        """convert this "flexible" value into a "normal" value.

        If *errors* is ``None``, pass on exceptions;
        otherwise return ``None`` and append exception information
        to *errors* (a list).
        """
        # must be defined by derived classes
        raise NotImplementedError

    def get_primary_value(self):
        pv = self
        while not isinstance(pv, PrimaryValue):
            pv = pv.wrapped
        return pv

    def get_raw_input(self):
        """return the unprocessed input value."""
        return self.get_primary_value().value

    def update_or_replace(self, value):
        """try to update ourself with "flexible" *value* and return success.

        Return values can be:

        `True`
            we could update ourself

        `None`
            indicates to the caller that it should replace ourself
            by *value*.

        `False`
            neither was an update possible nor is a replacement
            appropriate in all cases. The caller must handle this
            case.
        """
        my_usage = self.get_mark("usage")
        value_usage = value.get_mark("usage")
        if value_usage == "replace":
            return  # "replace" always replaces
        if value_usage == "conditional":
            # a conditional value is ignored if there is already a value
            return True
        act_as_default = my_usage in ("default", "conditional")
        # This implements that a default value can be overridden
        #  by a non default value but not by another default value
        if act_as_default == (value_usage == "default"):
            return bool(self.update(value))
        return None if act_as_default else False

    def update(self, value):
        """try to update ourself with *value*; return `True` if sucessful."""
        return  # not updatable


class PrimaryValue(FlexValue):
    """`FlexValue` describing the parameter value."""
    # special case for already recoded value
    form_encoding = site_encoding = None

    def __init__(self, value, name, converter, encoding, encodings):
        """wrap the request parameter value.

        *value* is the (mostly) unprocessed parameter value. An uploaded
        file, however, has already been wrapped as a `FileUpload`.

        *encoding* is the encoding explicitly specified
        for this request parameter, or ``None``.

        *encodings* is a ``dict`` with environment information
        about encodings. It has keys ``form_encoding`` specifying
        the encoding use by the HTTP client for the serialization
        of the form data and ``site_encoding`` specifying the
        encoding used by this instance.
        If *encodings* is ``None``, *value* is ready to use.
        """
        super(PrimaryValue, self).__init__(None)
        self.value = value
        self.name = name
        self.converter = converter
        self.encoding = encoding
        if encodings is not None:
            self.form_encoding = encodings["form_encoding"]
            self.site_encoding = encodings["site_encoding"]

    def instantiate(self, errors=None):
        try:
            return self._instantiate()
        except Exception:
            if errors is None:
                raise
            errors.append((self.name, self.value, exc_info()))
            return

    def _instantiate(self):
        value = self.value
        __traceback_info__ = value
        if isinstance(value, FileUpload):
            options = value.type_options
            if self.encoding:
                if "charset" not in options:
                    options["charset"] = self.encoding
                    if value.type is not None:
                        value.headers["content-type"] += \
                            "; charset=" + self.encoding
            if self.converter is None:
                return value
            # determine the encoding
            encoding = options["charset"] if "charset" in options else None
            # we do not use ``site_encoding`` here as the file content
            #  need not be in any relation to our configuration
            encoding = encoding or self.encoding
            return self._convert(value.read(), encoding)
        encoding = self.encoding or self.form_encoding or self.site_encoding
        # ``encoding is None`` means that *value* is ready to use
        if encoding is not None:
            # at this place, ``value`` is a sequences of bytes (PY2)
            #  or a "latin-1" decoded sequence of bytes (PY3)
            #  ensure, we get a sequence of bytes in all cases
            if PY3:
                value = value.encode("latin-1")
            # try to recode to text
            #   This may fail when ``encoding`` is not correct
            try:
                value = value.decode(encoding)
            except UnicodeDecodeError:
                if PY3 or self.encoding:
                    raise
                    # fall through for backward compatibility reasons
            # HTML5 allows to encode characters not covered by the
            #  form encoding as character references -- dereference
            value = dereference_character_references(value)
        if self.converter is None:
            if PY3 or self.encoding is not None:
                # the value should be text
                # Note: we interpret the presence of an explicit encoding
                #  as wish to get text (not bytes)
                return value
            elif isinstance(value, unicode):
                # convert to bytes
                #  like "HTML5", we use character references for
                #  unencodable characters.
                #  At least, ``PageTemplate`` works well with those references
                #  At other places, they might cause problems.
                value = value.encode(self.site_encoding, "xmlcharrefreplace")
            return value
        return self._convert(value, None)

    def _convert(self, value, encoding):
        """Apply the converter to *value* and *encoding*."""
        converter = self.converter
        input_types = getattr(converter, "input_types", (str,))
        if not isinstance(value, input_types):
            # we must recode
            if isinstance(value, bytes):
                value = value.decode(encoding or self.site_encoding)
            else:
                value = value.encode(encoding or self.site_encoding)

        if has_parameter(converter, "encoding"):
            # modern converter
            return converter(value, encoding)
        else:
            # legacy converter
            return converter(value)


class SequenceValue(FlexValue):
    """A "flexible" value representing a sequence of values."""

    # the sequence type of the instantiated value
    of_type = None

    MARK_TYPES = {"mode": ("append",)}

    def __init__(self, wrapped, of_type, explicit=True):
        super(SequenceValue, self).__init__(wrapped)
        self.components = [wrapped]
        self.of_type = of_type
        self.explicit = explicit

    def instantiate(self, errors=None):
        return self.of_type(w.instantiate(errors) for w in self.components)

    def update(self, value):
        """update with the first element of *value*.

        *value* usually must be a ``SequenceValue``.
        If this is not the case and *explicit* is false,
        *value* itself is used instead of its first element.

        If *value* uses append mode, then its first
        element is appended unconditionally.
        Otherwise, the update tries first to ``update_or_replace`` its
        last element and appends the new value if this is not possible.

        ``update`` always returns ``True``.
        """
        if self.explicit:
            if isinstance(value, SequenceValue):
                append_mode = value.get_mark("mode") == "append"
                value = value.components[0]
                if append_mode:
                    self.components.append(value)
                    return True
            else:
                raise TypeError("Incompatible `FlexValue` types",
                                self.__class__, value.__class__)
        return self._update_tail(value)

    def _update_tail(self, value):
        if not self.explicit and not isinstance(value, PrimaryValue):
            raise TypeError("implicit aggregation as list only supported for "
                            "elementary values, not "
                            + value.__class__.__name__)
        upd = self.components[-1].update_or_replace(value)\
            if self.components else False
        if upd is None:  # replace
            self.components[-1] = value
        elif upd is False:
            self.components.append(value)
        return True

    def update_or_replace(self, value):
        if self.explicit or value.get_mark("usage") == "replace":
            return super(SequenceValue, self).update_or_replace(value)
        # this sequence was implicitly created
        #   `value` is at the component level, not the list level
        return self._update_tail(value)


class RecordValue(FlexValue):
    """A "flexible" value representing a record of fields.

    A field has a *name* and a *value*.
    """

    # factory used for instantiation
    INST_FACTORY = record

    def __init__(self, wrapped, name):
        super(RecordValue, self).__init__(wrapped)
        self.mapping = {name: wrapped}

    def instantiate(self, errors=None):
        return self.INST_FACTORY(
            **dict((name, value.instantiate(errors))
                   for (name, value) in self.mapping.items()))

    def update(self, value):
        """update with the field of *value*.

        *value* must be a ``RecordValue`` with a single field
        *field_name*, *field_value*.

        If *field_name* does not yet exist, the new field is added.
        Otherwise it is tried to ``update_or_replace`` the
        existing field; ``update`` returns ``False`` if this
        fails. In all other cases, it returns ``True``.
        """
        if not isinstance(value, RecordValue):
            raise TypeError("Incompatible `FlexValue` types",
                            self.__class__, value.__class__)
        ((name, value),) = value.mapping.items()
        mapping = self.mapping
        if name not in mapping:
            mapping[name] = value
            return True
        ov = mapping[name]
        upd = ov.update_or_replace(value)
        if upd is True:  # updated
            return upd
        if upd is None:  # replace
            mapping[name] = value
            return True
        return self.handle_not_updatable(name, value)

    def handle_not_updatable(self, name, value):
        return False


class FormValue(RecordValue):
    """Top level request parameter record -- destined to become ``form``."""

    INST_FACTORY = dict

    def __init__(self):
        super(FlexValue, self).__init__()
        self.mapping = {}

    def add(self, name, value, aggs):
        """add *name*, *value* parameter, aggregated by *aggs*.

        *value* is a ``PrimaryValue``.

        *aggs* is the reversed list of aggregators to be applied.
        """
        while aggs:
            agg = aggs.pop()
            cont = agg.continuation(name, value, aggs)
            if cont is None:  # no value
                return
            name, value, aggs = cont  # how to continue
        return self.update_or_replace(RecordValue(value, name))

    def handle_not_updatable(self, name, value):
        # convert to an implicit sequence
        mapping = self.mapping
        ov = mapping[name]
        if not isinstance(ov, PrimaryValue):
            raise TypeError("implicit aggregation as list only supported for "
                            "elementary values, not " + ov.__class__.__name__)
        sv = SequenceValue(ov, list, False)
        sv._update_tail(value)
        mapping[name] = sv
        return True


class Aggregator(object):
    """Base ``Aggregator`` class."""
    def continuation(self, name, value, aggs):
        """transform *name*, *value* and *aggs*, or return `None`."""
        return self.tr_name(name), self.tr_value(value), self.tr_aggs(aggs)

    def tr_name(self, name):
        return name

    def tr_value(self, value):
        raise NotImplementedError()

    def tr_aggs(self, aggs):
        return aggs


class SequenceAggregator(Aggregator):
    def __init__(self, of_type):
        self.of_type = of_type

    def tr_value(self, value):
        return SequenceValue(value, self.of_type)


class RecordAggregator(Aggregator):
    def continuation(self, name, value, aggs):
        pp = name.rfind(".")
        if pp == -1:
            raise ValueError("missing `.` in record parameter", name)
        key, attr = name[:pp], name[pp + 1:]
        return key, RecordValue(value, attr), aggs


class MarkAggregator(Aggregator):
    def __init__(self, type, mark):
        self.type = type
        self.mark = mark

    def tr_value(self, value):
        value.mark(self.type, self.mark)
        return value


class EmptyAggregator(Aggregator):
    def tr_value(self, value):
        if not isinstance(value, SequenceValue):
            raise TypeError("`empty` can only be applied to a sequence, not "
                            + value.__class__.__name__)
        del value.components[:]
        return value


class IgnoreEmptyAggregator(Aggregator):
    def continuation(self, name, value, aggs):
        return (name, value, aggs) if value.get_raw_input() else None


class MethodAggregator(Aggregator):
    def continuation(self, name, value, aggs):
        if getattr(name, "img_control", False):
            # special "image" parameter
            if name.endswith(".y"):
                # we already have handled the ".x"
                return
            name = name[:-2]
            if not name:
                raise ValueError(
                    "*name* must not be empty for an image parameter"
                    " aggregated as `method`")
        if name:
            value = PrimaryValue(name, value.get_primary_value().name,
                                 None, None, None)
        return ("__method__", value, aggs)


class SynonymAggregator(Aggregator):
    def __init__(self, agg_names):
        """define as synonym of *agg_namess*."""
        self.rev_aggs = [aggregators[agg] for agg in reversed(agg_names)]

    def tr_aggs(self, aggs):
        return aggs + self.rev_aggs

    def tr_value(self, value):
        return value


aggregators = dict(
    # sequence aggregators
    list=SequenceAggregator(list),
    tuple=SequenceAggregator(tuple),
    empty=EmptyAggregator(),
    append=MarkAggregator("mode", "append"),
    # record aggregator
    record=RecordAggregator(),
    # value marking aggregators
    default=MarkAggregator("usage", "default"),
    replace=MarkAggregator("usage", "replace"),
    conditional=MarkAggregator("usage", "conditional"),
    # miscellaneous aggregators
    ignore_empty=IgnoreEmptyAggregator(),
    method=MethodAggregator(),
)
# add synonyms
for _ in (("records", ("record", "list")),
          ("default_method", ("method", "conditional")),
          ("action", ("method",)),
          ("default_action", ("default_method",)),
          ):
    aggregators[_[0]] = SynonymAggregator(_[1])


def process_parameters(params, site_encoding):
    """process *params* and return a corresponding variables dict and errors.

    *params* is a sequence of *name*, *value* pairs, each
    describing one parameter or a control (see below).

    *name* and *value* are typically native strings.
    For Python3, the native strings are actually "latin1" decoded
    byte sequences. The real encoding for *name* is initially
    *site_encoding*; a ``_charset_`` control parameter
    can change this encoding.

    The *name* of a parameter can contain an encoding directive
    which specifies the encoding used by the corresponding *value*.
    Otherwise, *value* uses the same encoding as *name*
    (if *value* is a native string).

    *value* can be a `FileUpload` instead of a native string.

    *site_encoding* must be an ASCII compatible encoding (not checked).


    Errors are reported via a list of triples *name*, *value* and *exc_info*.
    Because *exc_info* contains a traceback, a non empty error list
    contains a cyclic structure. There is a high risk that the
    garbage collector cannot reclaim the menory. Therefore, it
    is important to clear the error list explicitly to break up
    the cycle.
    """
    form = FormValue()
    errors = []
    form_encoding = site_encoding
    encodings = dict(site_encoding=site_encoding, form_encoding=form_encoding)
    img_y_index = -1
    for i, (name, value) in enumerate(params):
        __traceback_info__ = name
        try:
            if PY3:
                # Note: for PY2, we assume that *name* needs no recoding
                #  This is justified for pure ASCII names.
                name = name.encode("latin1").decode(form_encoding)
                # HTML5 uses xml character references to represent
                #  characters not representable by *form_encoding*.
                name = dereference_character_references(name)
                __traceback_info__ = name
            if name == "_charset_":
                # HTML5 uses this control to report the encoding
                #   of the form data
                # For HTML5, this is the encoding used for the complete
                #   form and applies to all parameters independent
                #   of position
                #   Instead, we use it to switch our *form_encoding* from
                #   this point on
                # For PY3, *value* at this place still represents
                #   a byte sequence
                #   i.e. it does not yet hold the correct text value
                #   However, HTML5 always uses an ASCII conpatible encoding
                #   and all encodings we support have ASCII names.
                #   For them, the proper recoding would not change anything.
                if is_encoding(value):
                    form_encoding = encodings["form_encoding"] = value
                    # We also put it into *form*
            key = name
            key_suffix = ""
            encoding = converter = None
            aggs = []
            if ":" in name:  # the parameter may have directives
                # Split *name* into *key* and a sequence of directives.
                # Support HTML's special "image" control handling
                #   HTML implements those controls as buttons.
                #   A click submits the form and the form data
                #   contains the image relative click position
                #   as two consecutive parameters *name*.x and *name*.y,
                #   where *name* is the control name.
                #   Those additional suffixes interfere with our
                #   directive suffixes and must be handled specially.
                # In the code below, we use that all encodings
                #   are ASCII compatible.
                if (i == img_y_index or (  # followup `.y` position
                    # starting `.x` position
                    i < len(params) - 1
                    and name.endswith(".x")
                    and params[i + 1][0] == name[:-2] + ".y"
                    and is_int(value) and is_int(params[i + 1][1]))
                ):  # noqa: E124
                    # This likely is a parameter from an image control
                    #   Split off the coordinate suffix
                    key_suffix = name[-2:]
                    name = name[:-2]
                    if i == img_y_index:
                        img_y_index = -1  # processed
                    else:
                        img_y_index = i + 1  # for y processing
                key, directives = split_directives(name).groups()
                # *directives* here is a string containing a sequence
                #   of directive candidates. We process those candidates
                #   from right to left and stop as soon as we do not
                #   know the candidate. The remaining candidates
                #   are put back onto *key*.
                #   This somewhat complicated approach is to allow
                #   the use of `:` as part of request variable names.
                directives = directives[1:].split(":") if directives else ()
                for di in range(len(directives), 0, -1):
                    d = directives[di - 1]
                    if d in aggregators:
                        aggs.append(aggregators[d])
                    elif d in type_converters:
                        if converter is not None:
                            raise ValueError("multiple converters")
                        converter = type_converters[d]
                    elif is_encoding(d):
                        if encoding is not None:
                            raise ValueError("multiple encodings")
                        encoding = d
                    else:
                        break  # candidate not recognized as a directive
                else:
                    di = 0
                if di > 0:
                    key += ":" + ":".join(directives[:di])
                if key_suffix:
                    key = mark_as_img_control(key + key_suffix)
            form.add(key,
                     PrimaryValue(value, name, converter, encoding, encodings),
                     aggs)
        except Exception:
            errors.append((name, value, exc_info()))
    form = form.instantiate(errors)
    return form, errors


is_int = compile(r'\s*-?\s*\d+\s*\Z').match
split_directives = compile(r'(.*?)((?::[a-zA-Z][-a-zA-Z0-9_]+)*)\Z').match

character_reference = compile(r'&#(\d+);')


def dereference_character_references(value):
    """replace character references in *value* by character.

    Do nothing, if *value* is not ``unicode`` (``str`` for PY3).
    """
    if isinstance(value, unicode):
        value = character_reference.sub(
            lambda m: chr(int(m.group(1))), value)
    return value


class WrappedStr(str):
    """An `str` with additional attributes."""


def mark_as_img_control(key):
    key = WrappedStr(key)
    key.img_control = True
    return key


def is_encoding(s):
    try:
        lookup(s)
        return True
    except LookupError:
        return False

if PY3:  # noqa: 
    unicode = str

    from inspect import signature

    def has_parameter(callable, param):
        return param in signature(callable).parameters
else:  # noqa: 
    from inspect import getargspec

    def has_parameter(callable, param):
        try:
            spec = getargspec(callable)
        except TypeError:
            spec = getargspec(callable.__call__)
        return param in spec.args

    FlexValue.__init_subclass__()
    SequenceValue.__init_subclass__()
