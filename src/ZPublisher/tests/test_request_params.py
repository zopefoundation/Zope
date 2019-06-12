# -*- coding: utf-8 -*-
from io import BytesIO
from six import PY3
from unittest import TestCase, skipIf

from ..HTTPRequest import FileUpload

from ..request_params import \
    process_parameters, record, RecordValue, SequenceValue, PrimaryValue

if PY3:
    unicode = str


class TestPrimaryValue(TestCase):
    encodings = dict(form_encoding="ascii", site_encoding="utf-8")

    def test_upload(self):
        # add missing charset
        v = PrimaryValue(self._mk_upload(b"", "text/plain"), "name",
                         None, "utf-8", self.encodings).instantiate()
        self.assertIsInstance(v, FileUpload)
        self.assertEqual(v.headers["content-type"],
                         "text/plain; charset=utf-8")
        self.assertEqual(v.type_options, dict(charset="utf-8"))
        # do not override existing `charset`
        v = PrimaryValue(self._mk_upload(b"", "text/plain; charset=utf-8"),
                         "name",
                         None, "latin1", self.encodings).instantiate()
        self.assertIsInstance(v, FileUpload)
        self.assertEqual(v.headers["content-type"],
                         "text/plain; charset=utf-8")
        self.assertEqual(v.type_options, dict(charset="utf-8"))
        bs = byte_sequence(128, 129, 130)
        # use upload provided charset, not ours
        v = PrimaryValue(self._mk_upload(bs, "text/plain; charset=latin1"),
                         "name",
                         to_text, "utf-8", self.encodings).instantiate()
        self.assertEqual(v, bs.decode("latin1"))
        # use our charset, not `site_encoding`
        v = PrimaryValue(self._mk_upload(bs),
                         "name",
                         to_text, "latin1", self.encodings).instantiate()
        self.assertEqual(v, bs.decode("latin1"))
        # our charset is irrelevant with `to_binary`
        v = PrimaryValue(self._mk_upload(bs),
                         "name",
                         to_binary, "utf-8", self.encodings).instantiate()
        self.assertEqual(v, bs)
        # do not use `site_encoding`
        self.assertInstantiateError(
            PrimaryValue(
                self._mk_upload(bs),
                "name",
                to_text, None,
                dict(form_encoding="latin1", site_encoding="latin1")
            ),
            UnicodeDecodeError)

    def _mk_upload(self, bs, ct=None):
        type, type_options = None, {}
        if ct is not None:
            ctcs = ct.split(";")
            type = ctcs[0]
            type_options = dict(ctc.strip().split("=") for ctc in ctcs[1:])
        return FileUpload(_O(file=BytesIO(bs),
                             headers={} if ct is None
                             else {"content-type": ct},
                             filename="filename",
                             name="name",
                             type=type, type_options=type_options,))

    def assertInstantiateError(self, value, exc):
        errors = []
        value.instantiate(errors)
        if not errors:
            self.fail("failed to raise an exception")
        self.assertIsInstance(errors[0][2][1], exc)

    def test_encoding(self):
        encodings = self.encodings
        uv = u'äöü'
        value = uv.encode('utf-8')
        if PY3:
            value = uv.encode('utf-8').decode("latin1")
        # form over site encoding
        if PY3:
            self.assertInstantiateError(
                PrimaryValue(value, "name", None, None, encodings),
                UnicodeDecodeError)
        else:
            # for backward compatibility reasons, we return `value` unchanged
            v = PrimaryValue(value, "name",
                             None, None, encodings).instantiate()
            self.assertEqual(v, value)
        # explicit over form encoding
        v = PrimaryValue(value, "name", None, "utf-8", encodings).instantiate()
        # Note: we return text even for Python 2 (due to the explciit encoding)
        self.assertEqual(v, uv)
        # test to_binary
        v = PrimaryValue(value, "name",
                         to_binary, "utf-8", encodings).instantiate()
        self.assertEqual(v, byte_sequence(*map(ord, uv)))
        # test to_text
        v = PrimaryValue(value, "name",
                         to_text, "utf-8", encodings).instantiate()
        self.assertEqual(v, uv)

    def test_converter_local_recoding(self):
        def converter(value):
            return value
        bs = byte_sequence(128, 129, 130)
        encodings = self.encodings
        # bytes --> str
        if PY3:
            v = PrimaryValue(self._mk_upload(bs), "name",
                             converter, "latin1", encodings).instantiate()
            self.assertEqual(v, bs.decode("latin1"))
        # text --> bytes
        # Note: we have currently no way to specify an
        #  output encoding for the conversion to "bytes" (`PrimaryValue`'s
        #  `encoding` parameter specifies the input encoding).
        #  The "local_recoding" uses `site_encoding`.
        value = bs
        if PY3:
            value = bs.decode("latin1")
        converter.input_types = bytes,
        v = PrimaryValue(value, "name",
                         converter, "latin1", encodings).instantiate()
        self.assertEqual(
            v,
            bs.decode("latin1").encode(encodings["site_encoding"]))

    @skipIf(PY3, "Python 3 needs no recoding")
    def test_value_local_recoding(self):
        uv = u"ä".encode("utf-8")
        pv = _make_pv(uv).instantiate()
        self.assertEqual(pv, uv)
        # test character reference
        pv = PrimaryValue(uv, "name", None, None,
                          dict(form_encoding="utf-8", site_encoding="ascii")
                          ).instantiate()
        self.assertEqual(pv, "&#228;")

    def test_preprocessed(self):
        v = PrimaryValue('abc', "name", None, None, None).instantiate()
        self.assertEqual(v, 'abc')

    def test_update_or_replace(self):
        # default, non-default combinations
        for td, ud in ((td, ud)
                       for td in (True, False)
                       for ud in (True, False)):
            tv = _make_pv("", td and "default" or None)
            uv = _make_pv("", ud and "default" or None)
            r = tv.update_or_replace(uv)
            if td and not ud:
                self.assertIsNone(r)
            else:
                self.assertIs(r, False)
        # conditional
        self.assertIs(_make_pv("", "conditional").update_or_replace(
            _make_pv("", "conditional")), True)
        # replace
        self.assertIsNone(_make_pv("", "replace").update_or_replace(
            _make_pv("", "replace")))


encodings = dict(form_encoding="utf-8", site_encoding="utf-8")


def _make_pv(v, mark=None):
    """make primary value from native string *v*."""
    if PY3:
        v = v.encode("utf-8").decode("latin-1")
    value = PrimaryValue(v, "name", None, None, encodings)
    if mark:
        value.mark("usage", mark)
    return value


pve = _make_pv("")
pvd = _make_pv("", mark="default")


def _make_sv(v=pve, of_type=list):
    """make sequence value."""
    return SequenceValue(v, of_type)


def _make_rv(v=pve, n="x"):
    return RecordValue(v, n)


class TestCompositeValues(TestCase):
    def test_seqeunce_instantiate(self):
        self.assertEqual(_make_sv().instantiate(), [""])
        self.assertEqual(_make_sv(of_type=tuple).instantiate(), ("",))

    def test_explicit_sequence(self):
        # incompatible types
        with self.assertRaises(TypeError):
            _make_sv().update(pve)
        # overwrite default element by non default
        tv = _make_sv(pvd)
        self.assertTrue(tv.update(_make_sv()))
        self.assertEqual(tv.components, [pve])
        # overwrite conditional element by non default
        tv = _make_sv(_make_pv("", "conditional"))
        self.assertTrue(tv.update(_make_sv()))
        self.assertEqual(tv.components, [pve])
        # but not in "append mode"
        tv = _make_sv(_make_pv("", "conditional"))
        uv = _make_sv()
        uv.mark("mode", "append")
        self.assertTrue(tv.update(uv))
        self.assertEqual(len(tv.components), 2)
        # replace replaces the last element
        tv = _make_sv()
        rv = _make_pv("", "replace")
        self.assertTrue(tv.update(_make_sv(rv)))
        self.assertEqual(tv.components, [rv])
        # append in all other cases
        tv = _make_sv()
        self.assertTrue(tv.update(_make_sv(pvd)))
        self.assertEqual(tv.components, [pve, pvd])
        tv = _make_sv()
        self.assertTrue(tv.update(_make_sv()))
        self.assertEqual(tv.components, [pve, pve])
        self.assertTrue(tv.update(_make_sv(pvd)))
        self.assertEqual(tv.components, [pve, pve, pvd])
        # empty sequence can be updated, but not update
        tv = _make_sv()
        ev = _make_sv()
        del ev.components[:]
        with self.assertRaises(IndexError):
            tv.update(ev)
        self.assertTrue(ev.update(tv))
        self.assertEqual(ev.components, [pve])

    def test_implicit_sequence(self):
        tv = _make_sv()
        tv.explicit = False
        # append of simple value
        self.assertIs(tv.update_or_replace(pve), True)
        self.assertEqual(tv.components, [pve, pve])
        # override of default value
        tv = _make_sv(pvd)
        tv.explicit = False
        self.assertIs(tv.update_or_replace(pve), True)
        self.assertEqual(tv.components, [pve])
        # replace replaces the whole list
        self.assertIsNone(tv.update_or_replace(_make_pv("", mark="replace")))
        # wrong type
        with self.assertRaises(TypeError):
            tv.update(_make_sv())

    def test_record_instantiate(self):
        self.assertEqual(_make_rv().instantiate().x, "")

    def test_record_update(self):
        tr = _make_rv(pvd)
        # new field
        self.assertTrue(tr.update(_make_rv(pve, "y")))
        self.assertEqual(tr.mapping, dict(x=pvd, y=pve))
        # override default
        self.assertTrue(tr.update(_make_rv()))
        self.assertEqual(tr.mapping, dict(x=pve, y=pve))
        # non updatable
        self.assertIs(tr.update(_make_rv()), False)
        self.assertEqual(tr.mapping, dict(x=pve, y=pve))
        # updatable
        tr = _make_rv(_make_sv())
        self.assertTrue(tr.update(_make_rv(_make_sv())))
        self.assertEqual(tr.mapping["x"].components, [pve, pve])
        # override conditional
        pvc = _make_pv("", "conditional")
        tr = _make_rv(pvc)
        self.assertTrue(tr.update(_make_rv(pve)))
        self.assertEqual(tr.mapping, dict(x=pve))
        # overriding conditional ignored
        self.assertTrue(tr.update(_make_rv(pvc)))
        self.assertEqual(tr.mapping, dict(x=pve))
        # replace overrides
        pvr = _make_pv("", "replace")
        self.assertTrue(tr.update(_make_rv(pvr)))
        self.assertEqual(tr.mapping, dict(x=pvr))


class TestProcessParameters(TestCase):
    def setUp(self):
        self.addTypeEqualityFunc(record, 'assertRecordEqual')

    def assertRecordEqual(self, r1, r2):
        self.assertEqual(r1.mapping, r2.mapping)

    def test_simple(self):
        self._check("x=1", dict(x="1"))

    def test_simple_multiple(self):
        # 2 x
        self._check("x=1&x=2", dict(x=["1", "2"]))
        # 3 x
        self._check("x=1&x=2&x=3", dict(x=["1", "2", "3"]))
        # 4 x
        self._check("x=1&x=2&x=3&x=4", dict(x=["1", "2", "3", "4"]))
        # only elementary
        with self.assertRaises(TypeError):
            self._check("x.a:record=1&x.a:record=2", {})
        with self.assertRaises(TypeError):
            self._check("x=1&x.a:record=2", {})
        with self.assertRaises(TypeError):
            self._check("x=1&x:list=2", {})
        # replace replaces the whole list
        self._check("x=1&x=2&x:replace=3", dict(x="3"))
        self._check("x=1&x=2&x:replace=3&x=4", dict(x=["3", "4"]))
        self._check("x=1&x=2&x:replace=3&x=4&x:replace=5", dict(x="5"))

    def test_conditional(self):
        self._check("x:conditional=1", dict(x="1"))
        self._check("x:conditional=1&x=2", dict(x="2"))
        self._check("x=2&x:conditional=1", dict(x="2"))
        self._check("x:default=2&x:conditional=1", dict(x="2"))
        self._check("x:conditional=2&x:default=1", dict(x=["2", "1"]))

    def test_replace(self):
        self._check("x:replace=1", dict(x="1"))
        self._check("x=2&x:replace=1", dict(x="1"))
        self._check("x:replace=2&x:replace=1", dict(x="1"))
        self._check("x:replace=1&x=2", dict(x=["1", "2"]))
        self._check("x:replace=1&x=2&x:replace=3", dict(x="3"))

    def test_empty(self):
        self._check("x:list:empty=", dict(x=[]))
        self._check("x:list:empty:list=", dict(x=[[]]))
        # append to empty list
        self._check("x:list:empty=&x:list=1", dict(x=["1"]))
        # empty list cannot update
        with self.assertRaises(IndexError):
            self._check("x:list=1&x:list:empty=", {})
        # empty can only be applied to a sequence
        with self.assertRaises(TypeError):
            self._check("x:empty=", {})

    def test_append(self):
        self._check("x:default:list=1&x:list:append=2", dict(x=["1", "2"]))
        # append can only be applied to a sequence
        with self.assertRaises(TypeError):
            self._check("x:append=", {})

    def test_converter(self):
        self._check("x:int=1", dict(x=1))
        # converter error
        with self.assertRaises(ValueError):
            self._check("x:required=", {})
        # multiple converter error
        with self.assertRaises(ValueError):
            self._check("x:required=&y:required=", {}, err_count=2)
        with self.assertRaises(ValueError):
            self._check("x:required=&x:required=", {}, err_count=2)

    def test_encoding(self):
        self._check("x:latin1=1", dict(x=u"1"))

    def test_encoding_converter(self):
        self._check("x:latin1:bytes= ", dict(x=byte_sequence(32)))

    def test_list(self):
        self._check("x:int:list=1", dict(x=[1]))
        # aggs/converter order is not important
        self._check("x:list:int=1", dict(x=[1]))

    def test_tuple(self):
        self._check("x:int:tuple=1", dict(x=(1,)))

    def test_record(self):
        self._check("x.a:int:record=1&x.b:record=b",
                    dict(x=record(a=1, b="b")))

    def test_ignore_empty(self):
        self._check("x:ignore_empty=", dict())

    def test_default(self):
        self._check("x:default:int=1&x=2", dict(x="2"))
        # parameter order is important
        self._check("x=2&x:default:int=1", dict(x=["2", 1]))
        # agg/converter order is not important
        self._check("x=2&x:int:default=1", dict(x=["2", 1]))
        # aggs order is important
        self._check("x.a:default:record=a&x.b:record=b",
                    dict(x=record(a="a", b="b")))
        self._check("x.a:record:default=a&x.b:record=b",
                    dict(x=record(b="b")))
        # double ":default"
        with self.assertRaises(ValueError):
            self._check("x:default:default=1", {})
        # implicit multi default list coercion
        self._check("x:int:default=3&x:int:default=4", dict(x=[3, 4]))
        self._check("x:int:default=3&x:int:default=4&x:int:default=5",
                    dict(x=[3, 4, 5]))
        # implicit default list coercion with override
        self._check("x:int:default=3&x:int:default=4&x:int:default=5&"
                    "x:int=1&x:int=2",
                    dict(x=[3, 4, 1, 2]))

    def test_method(self):
        # from value
        self._check(":method=method", dict(__method__="method"))
        # from name
        self._check("name:method=method", dict(__method__="name"))

    def test_records(self):
        self._check("x.a:records=a1&x.a:records=a2",
                    dict(x=[record(a="a1"), record(a="a2")]))

    def test_default_method(self):
        self._check("name:default_method=method",
                    dict(__method__="name"))
        self._check("name:default_method=method&:method=value",
                    dict(__method__="value"))
        self._check(":method=value&name:default_method=method",
                    dict(__method__="value"))

    def test_action(self):
        self._check("name:default_action=method&:action=value",
                    dict(__method__="value"))

    def test_img_control(self):
        # must have non empty name
        with self.assertRaises(ValueError):
            self._check(":method.x=10&:method.y=22", {})
        # proper image control
        self._check("name:method.x=10&name:method.y=22",
                    dict(__method__="name"))
        self._check("name:int:record.x=10&name:int:record.y=22",
                    dict(name=record(x=10, y=22)))
        # no image controls
        #  missing .y
        self._check("name:int:record.x=10",
                    {"name:int:record.x": "10"})
        #  no integer values
        self._check("name:record.x=x&name:record.y=22",
                    {"name:record.x": "x", "name:record.y": "22"})
        self._check("name:record.x=10&name:record.y=y",
                    {"name:record.x": "10", "name:record.y": "y"})

    def test_unrecognized_directive(self):
        self._check("x:xxxxx=1", {"x:xxxxx": "1"})
        self._check("x:xxxxx:int=1", {"x:xxxxx": 1})
        self._check("x:int:xxxxx=1", {"x:int:xxxxx": "1"})

    def test_charset_(self):
        # "utf-8" form, "ascii" site encoding
        qs = u"_charset_=utf-8&x=ä"
        x = u"ä"
        if not PY3:
            qs = qs.encode("utf-8")
            x = "&#%d;" % ord(x)
        self._check(qs, dict(_charset_="utf-8", x=x))
        if not PY3:
            # "latin1" form, "utf-8" site encoding
            qs = u"_charset_=latin1&x=ä".encode("latin1")
            x = u"ä"
            self._check(qs,
                        dict(_charset_="latin1", x=x.encode("utf-8")),
                        "utf-8"
                        )

    def test_nested_checkboxes(self):
        self._check(
            "x.a:default:records=d&x.b:records=1"
            "&x.a:default:records=d&x.a:records=2&x.b:records=2",
            dict(x=[record(a="d", b="1"), record(a="2", b="2")]))

    def test_implicit_explicit_sequence(self):
        # no *param* followed by *param*:list
        with self.assertRaises(TypeError):
            self._check("x=1&x:list=2", {})
        with self.assertRaises(TypeError):
            self._check("x=1&x=2&x:list=2", {})
        # no *param*:list followed by *param*
        with self.assertRaises(TypeError):
            self._check("x=1&x:list=2", {})

    def test_round_trip(self):
        r = record
        self._rtcheck(dict(x="1"))
        self._rtcheck(dict(x="1", y="2"))
        self._rtcheck(dict(x=[]))
        self._rtcheck(dict(x=["1", ["2", "3"], "4", [], "5"]))
        self._rtcheck(dict(x=r(a=["1", ["2", "3"], "4"], b="5")))
        self._rtcheck(dict(x=["0",
                              r(a="a", c="c"),
                              r(a=["1", ["2", "3"], "4", [], "5"], b="5")]))
        # records with different keys
        self._rtcheck(dict(x=[r(a="a"), r(b="b")]))

    def test_bytes_634(self):
        # checks https://github.com/zopefoundation/Zope/issues/634
        byts = byte_sequence(128, 129, 130)
        nbyts = byts.decode("latin-1") if PY3 else byts
        self._check((("x:latin1:bytes", nbyts),), dict(x=byts))

    @skipIf(not PY3, "for Python 2, parameter names should be ASCII only")
    def test_character_reference(self):
        self._check([("&#228;", "1")], {"ä": "1"})

    def _check(self, params, expected, encoding="ascii", err_count=None):
        if isinstance(params, str):
            if PY3:
                params = params.encode("utf-8").decode("latin1")
            params = [param.split("=") for param in params.split("&")]
        form, errors = process_parameters(params, encoding)
        if err_count is not None:
            self.assertEqual(len(errors), err_count)
        if errors:
            self.assertEqual(len(errors), err_count or 1)
            raise errors[0][2][1]
        self.assertEqual(form, expected)

    def _rtcheck(self, d):
        self._check(mkq(d), d)


def byte_sequence(*byts):
    """turn bytes *byts* into a bytes sequence."""
    if PY3:
        return bytes(byts)
    else:
        return "".join(map(chr, byts))


class _O(object):
    """Auxiliary to create an object from keywords."""
    def __init__(self, **kw):
        self.__dict__.update(kw)


def to_binary(v, encoding=None):
    return v.encode(encoding or "latin1") if isinstance(v, unicode) else v


to_binary.input_types = bytes, unicode,


def to_text(v, encoding=None):
    return v if isinstance(v, unicode) else v.decode(encoding or "ascii")


to_text.input_types = bytes, unicode,


def mkq(d):
    """make query representing ``dict`` *d*)."""
    def _mk(v, top=False):
        """*v* --> sequwnce of triples *name*, *directives*, *value*."""
        if isinstance(v, str):
            return ("", "", v),
        elif isinstance(v, list):
            if not v:
                return ("", ":list:empty", ""),
            params = []
            for x in v:
                pl = len(params)
                params.extend((p[0], p[1] + ":list", p[2])
                              for p in _mk(x))
                # ensure a new list element is started
                p1 = params[pl]
                params[pl] = (p1[0], p1[1] + ":append", p1[2])
            return params
        elif hasattr(v, "items"):
            params = []
            name_prefix, directive_suffix = \
                ("", "") if top else (".", ":record")
            for k, kv in v.items():
                params.extend((name_prefix + k + p[0],
                               p[1] + directive_suffix,
                               p[2]) for p in _mk(kv))
            return params
        else:
            raise NotImplementedError(v)
    return "&".join("%s%s=%s" % p for p in _mk(d, True))
