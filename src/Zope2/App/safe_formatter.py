from AccessControl import allow_type
from AccessControl.ZopeGuards import guarded_getattr
from collections import Mapping

import string


class _MagicFormatMapping(Mapping):
    """
    Pulled from Jinja2

    This class implements a dummy wrapper to fix a bug in the Python
    standard library for string formatting.

    See http://bugs.python.org/issue13598 for information about why
    this is necessary.
    """

    def __init__(self, args, kwargs):
        self._args = args
        self._kwargs = kwargs
        self._last_index = 0

    def __getitem__(self, key):
        if key == '':
            idx = self._last_index
            self._last_index += 1
            try:
                return self._args[idx]
            except LookupError:
                pass
            key = str(idx)
        return self._kwargs[key]

    def __iter__(self):
        return iter(self._kwargs)

    def __len__(self):
        return len(self._kwargs)


class SafeFormatter(string.Formatter):

    def __init__(self, value):
        self.value = value
        super(SafeFormatter, self).__init__()

    def get_field(self, field_name, args, kwargs):
        """
        Here we're overridding so we can use guarded_getattr instead of
        regular getattr
        """
        first, rest = field_name._formatter_field_name_split()

        obj = self.get_value(first, args, kwargs)

        # loop through the rest of the field_name, doing
        #  getattr or getitem as needed
        for is_attr, i in rest:
            if is_attr:
                obj = guarded_getattr(obj, i)
            else:
                obj = obj[i]

        return obj, first

    def safe_format(self, *args, **kwargs):
        kwargs = _MagicFormatMapping(args, kwargs)
        return self.vformat(self.value, args, kwargs)


def safe_format(inst, method):
    """
    Use our SafeFormatter that uses guarded_getattr for attribute access
    """
    return SafeFormatter(inst).safe_format


def _load_allow_type_for_string_types():
    # We want to allow all methods on string type except "format".
    # That one needs special handling to avoid access to attributes.
    # from Products.PageTemplates.safe_formatter import safe_format
    rules = dict([(m, True) for m in dir(str) if not m.startswith('_')])
    rules['format'] = safe_format
    allow_type(str, rules)

    # Same for unicode instead of str.
    rules = dict([(m, True) for m in dir(unicode) if not m.startswith('_')])
    rules['format'] = safe_format
    allow_type(unicode, rules)
