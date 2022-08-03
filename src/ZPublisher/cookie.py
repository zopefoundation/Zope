##############################################################################
#
# Copyright (c) 2022 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""HTTP cookie support.

The implementation is based on
`RFC6265 <https://www.rfc-editor.org/rfc/rfc6265.html>`_.

The module introduces 2 features:

 1. default ``ICookieParamPolicy`` and ``ICookieValuePolicy``
 2. a cookie parameter registry

and exports the functions ``getCookieParamPolicy``, ``getCookieValuePolicy``
``registerCookieParameter``,
``normalizeCookieParameterName`` and ``convertCookieParameter``.
"""
import datetime
from encodings.idna import ToASCII
from encodings.idna import nameprep
from itertools import chain
from re import compile
from time import time
from urllib.parse import quote
from urllib.parse import unquote

from Acquisition import aq_base
from DateTime import DateTime
from zope.component import getGlobalSiteManager
from zope.component import queryUtility
from zope.interface import implementer

from .interfaces import ICookieParamPolicy
from .interfaces import ICookieValuePolicy


@implementer(ICookieParamPolicy)
class DefaultCookieParamPolicy:
    """Default ``ICookieParamPolicy``.

    It adds ``Expires`` when it sees ``Max-Age`` (for compatibility
    with HTTP/1.0).
    """

    @staticmethod
    def parameters(name, attrs):
        """adds ``Expires`` if not present and ``Max-Age`` is set."""
        for pn, pv in attrs.items():
            if pn != "value":
                yield (pn, pv)
        if "Expires" not in attrs and attrs.get("Max-Age") is not None:
            max_age = int(attrs["Max-Age"])
            expires = "Wed, 31 Dec 1997 23:59:59 GMT" if max_age <= 0 \
                      else time() + max_age
            yield convertCookieParameter("Expires", expires)

    @staticmethod
    def check_consistency(name, attrs):
        return  # does not enforce any consistency rules


defaultCookieParamPolicy = DefaultCookieParamPolicy()


@implementer(ICookieValuePolicy)
class DefaultCookieValuePolicy:
    """Default ``ICookieValuePolicy``."""

    @staticmethod
    def dump(name, value):
        """simply quote *value*."""
        return quote(value)

    @staticmethod
    def load(name, value):
        """simply unquote *value*."""
        return unquote(value)


defaultCookieValuePolicy = DefaultCookieValuePolicy()


def getCookieParamPolicy():
    return queryUtility(ICookieParamPolicy, default=defaultCookieParamPolicy)


def getCookieValuePolicy():
    # we look this utility up only in the global component registry
    # as at the time of cookie parsing (when ``load`` is used),
    # it is the only component registry available
    return getGlobalSiteManager().queryUtility(
        ICookieValuePolicy, default=defaultCookieValuePolicy)


class CookieParameterRegistry:
    """The cookie parameter registry maps parameter names.

    It maintains 2 maps: one to normalize parameter names
    and one to check and convert parameter values.
    """
    def __init__(self):
        self._normalize = {}
        self._convert = {}

    def register(self, name, converter, aliases=()):
        """register cookie parameter *name* with *converter* and *aliases*.

        *converter* is a function which will be applied to
        parameter values and which is expected to either
        raise an exception or convert the value into
        either ``None``, ``True``
        or an ASCII string without control characters and ``;``.
        ``None`` means "drop the parameter",
        ``True`` means "drop the parameter value",
        otherwise, the return value is used as value representation.

        Some aliases are automatically derived from *name*:
        convertion to lower, ``-`` to ``_`` conversion.
        Further aliases can be defined via *aliases*.

        It is not an error to override existing registrations.
        """
        self._convert[name] = converter
        for n in chain((name,), aliases):
            for ln in (n, n.lower()):
                for a in (ln, ln.replace("-", "_")):
                    self._normalize[a] = name

    def convert(self, name, value):
        """check and convert *name* and *value* for parameter *name*.

        Raises an exception in case of errors; otherwise,
        returns *normalized name*, *converted value*.

        The normalized name is the official parameter name.
        The converted (or normalized) value is either ``None``
        (drop the parameter), ``True`` (drop the parameter value)
        or an ASCII string (use as parameter value).
        """
        nn = self.normalizeName(name)
        return nn, (value if value is None else self[nn](value))

    def normalizeName(self, name):
        return self._normalize[name.lower()]

    def __getitem__(self, name):
        return self._convert[name]


cookieParameterRegistry = CookieParameterRegistry()
registerCookieParameter = cookieParameterRegistry.register
convertCookieParameter = cookieParameterRegistry.convert
normalizeCookieParameterName = cookieParameterRegistry.normalizeName


###############################################################################
# Cookie parameter converters

# ``Expires``
class UTC(datetime.tzinfo):
    ZERO = datetime.timedelta(0)

    def utcoffset(self, dt):
        return self.ZERO

    def tzname(self, dt):
        return "UTC"

    dst = utcoffset


utc = UTC()

wdmap = dict(enumerate("Mon Tue Wed Thu Fri Sat Sun".split()))
mmap = {i + 1: m for (i, m) in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}


def rfc1123_converter(value):
    """convert *value* into an RFC1123 date.

    *value* can be a string (assumed already in the required form),
    a Python `datetime` (assumed to be in the UTC time zone, if naive),
    a float (interpreted as time stamp),
    or a `DateTime` object.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        value = datetime.datetime.utcfromtimestamp(value)
    elif isinstance(value, DateTime):
        value = value.toZone("GMT").asdatetime()
    if not isinstance(value, datetime.datetime):
        raise ValueError("unsupported type: %s" % type(value))
    if value.utcoffset() is not None:
        value = value.astimezone(utc)
    tt = value.timetuple()
    # we cannot use ``strftime`` because it depends on locale
    return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (
        wdmap[tt.tm_wday],
        tt.tm_mday, mmap[tt.tm_mon], tt.tm_year,
        tt.tm_hour, tt.tm_min, tt.tm_sec)


registerCookieParameter("Expires", rfc1123_converter)


# ``Max-Age``
def int_converter(value):
    """check for *int* value."""
    int(value)
    return str(value)


registerCookieParameter("Max-Age", int_converter)


# ``Domain``
def domain_converter(value):
    """convert *value* into an internationalized domain name.

    Note: The Python infrastructure supports IDNA2003, but
    RFC6265 calls for IDNA2008. IDNA2008 is implemented by
    a third party module. You might want to override
    the registration to get IDNA2008 if you observe domain
    related problems.
    """
    # Python 2 requires unicode
    u_value = value.decode("utf-8") if isinstance(value, bytes) else value
    if "xn--" in u_value:  # already encoded
        return value

    # According to https://www.rfc-editor.org/rfc/rfc6265#section-4.1.2.3 a
    # leading dot is ignored. If it is there `ToASCII`, breaks on the empty
    # string:
    u_value = u_value.lstrip('.')
    return ".".join(to_str(ToASCII(nameprep(c))) for c in u_value.split("."))


registerCookieParameter("Domain", domain_converter)


# ``Path``
path_safe = compile("["
                    "-_.!~*'()"  # RFC 2396 section 2.3 (unreserved)
                    "a-zA-Z0-9"  # letters and digits
                    "/:@&=+$,"   # RFC 2396 section 3.3 (path reserved)
                                 # excluding ``;``
                    "]*$").match


def path_converter(value):
    """convert *value* to a cookie path.

    The convertion is based on ``absolute_url_path``.
    If *value* lacks this method, it is assumed to be a string.
    If the string contains ``%``, it is used as is; otherwise,
    it may be quoted by Python's ``urllib.parse.quote``.

    **Note**:
    According to RFC 6265 section 5.1.4 a cookie path match **does not**
    unquote its arguments. It is therefore important to use
    the same quoting algorithm for the URL and the cookie path.
    If the cookie path contains only allowed characters
    (RFC 2396 unreserved (section 2.3) and
    RFC 2396 path special characters (section 3.3) excluding ``;``),
    the value is taken verbatim; otherwise it is quoted
    by Python's `urllib.parse.quote` (which
    is used by `OFS.Traversable` as its ULR quoting). It quotes
    all special characters apart from ``-_./``.
    Quote yourself if this does not match your URL quoting.
    """
    ap = getattr(aq_base(value), "absolute_url_path", None)
    if ap is not None:
        return value.absolute_url_path()
    if "%" in value or path_safe(value):
        return value
    return quote(value)


registerCookieParameter("Path", path_converter)


# boolean parameters: ``httpOnly``, ``Secure``
def bool_converter(value):
    return bool(value) or None


registerCookieParameter("HttpOnly", bool_converter, ("http_only",))
registerCookieParameter("Secure", bool_converter)


# selection paramters
class SelectionConverter:
    def __init__(self, *valid):
        self.valid = valid
        self.check = [v.lower() for v in valid]

    def __call__(self, value):
        i = self.check.index(value.lower())
        return self.valid[i]


registerCookieParameter("SameSite",
                        SelectionConverter("None", "Lax", "Strict"),
                        ("same_site",))


# comment -- string converter
contains_bad_char = compile("[\x00-\x1f;]").search


def str_converter(value):
    """*value* should contain only ASCII characters."""
    if not isinstance(value, str):
        if hasattr(value, "encode"):  # Python 2 unicode
            value = value.encode("iso-8859-1", "replace")
        else:
            value = str(value)
    # RFC 6265 requires ASCII characters excluding controls and ``;``.
    # We do not enforce ASCII; if `str` contains non iso-8859-1 characters
    # we will get an exception later on
    # If necessary, we might use the ``header_encoding_registry``
    # to remove this restriction.
    if contains_bad_char(value):
        raise ValueError(
            "``;`` and controls are not allowed in cookie parameters")
    return value


# Comment is not defined by RFC 6265; maybe something Zope special
registerCookieParameter("Comment", str_converter)


###########################################################################
# Auxiliaries
def to_str(s):
    """convert bytes to ``str``."""
    if not isinstance(s, str):
        s = s.decode("utf-8")
    return s
