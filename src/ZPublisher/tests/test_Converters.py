##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import unittest
import warnings


class ConvertersTests(unittest.TestCase):

    def test_field2boolean_with_empty_string(self):
        from ZPublisher.Converters import field2boolean
        to_convert = ''
        expected = False
        self.assertEqual(field2boolean(to_convert), expected)

    def test_field2boolean_with_False_as_string(self):
        from ZPublisher.Converters import field2boolean
        to_convert = 'False'
        expected = False
        self.assertEqual(field2boolean(to_convert), expected)

    def test_field2boolean_with_some_string(self):
        from ZPublisher.Converters import field2boolean
        to_convert = 'to_convert'
        expected = True
        self.assertEqual(field2boolean(to_convert), expected)

    def test_field2boolean_with_positive_int(self):
        from ZPublisher.Converters import field2boolean
        to_convert = 1
        expected = True
        self.assertEqual(field2boolean(to_convert), expected)

    def test_field2boolean_with_zero(self):
        from ZPublisher.Converters import field2boolean
        to_convert = 0
        expected = False
        self.assertEqual(field2boolean(to_convert), expected)

    def test_field2boolean_with_empty_list(self):
        from ZPublisher.Converters import field2boolean
        to_convert = []
        expected = False
        self.assertEqual(field2boolean(to_convert), expected)

    def test_field2float_with_list_of_numbers(self):
        from ZPublisher.Converters import field2float
        to_convert = ["1.1", "2.2", "3.3"]
        expected = [1.1, 2.2, 3.3]
        rv = field2float(to_convert)
        self.assertEqual(rv[0], expected[0])
        self.assertEqual(rv[1], expected[1])
        self.assertEqual(rv[2], expected[2])

    def test_field2float_with_regular_number(self):
        from ZPublisher.Converters import field2float
        to_convert = "1"
        expected = 1.0
        self.assertAlmostEqual(field2float(to_convert), expected)

    def test_field2float_with_illegal_value(self):
        from ZPublisher.Converters import field2float
        to_convert = "<"
        self.assertRaises(ValueError, field2float, to_convert)

    def test_field2float_with_empty_value(self):
        from ZPublisher.Converters import field2float
        to_convert = ""
        self.assertRaises(ValueError, field2float, to_convert)

    def test_field2int_with_list_of_numbers(self):
        from ZPublisher.Converters import field2int
        to_convert = ["1", "2", "3"]
        expected = [1, 2, 3]
        self.assertEqual(field2int(to_convert), expected)

    def test_field2int_with_regular_number(self):
        from ZPublisher.Converters import field2int
        to_convert = "1"
        expected = 1
        self.assertEqual(field2int(to_convert), expected)

    def test_field2int_with_illegal_value(self):
        from ZPublisher.Converters import field2int
        to_convert = "<"
        self.assertRaises(ValueError, field2int, to_convert)

    def test_field2int_with_empty_value(self):
        from ZPublisher.Converters import field2int
        to_convert = ""
        self.assertRaises(ValueError, field2int, to_convert)

    def test_field2long_with_list_of_numbers(self):
        from ZPublisher.Converters import field2long
        to_convert = ["1", "2", "3"]
        expected = [1, 2, 3]
        self.assertEqual(field2long(to_convert), expected)

    def test_field2long_with_regular_number(self):
        from ZPublisher.Converters import field2long
        to_convert = "1"
        expected = 1
        self.assertEqual(field2long(to_convert), expected)

    def test_field2long_with_illegal_value(self):
        from ZPublisher.Converters import field2long
        to_convert = "<"
        self.assertRaises(ValueError, field2long, to_convert)

    def test_field2long_with_empty_value(self):
        from ZPublisher.Converters import field2long
        to_convert = ""
        self.assertRaises(ValueError, field2long, to_convert)

    def test_field2long_strips_trailing_long_symbol(self):
        from ZPublisher.Converters import field2long
        to_convert = "2L"
        expected = 2
        self.assertEqual(field2long(to_convert), expected)

    def test_field2required_returns_string(self):
        from ZPublisher.Converters import field2required
        to_convert = "to_convert"
        expected = "to_convert"
        self.assertEqual(field2required(to_convert), expected)

    def test_field2required_raises_ValueError(self):
        from ZPublisher.Converters import field2required
        value = ""
        self.assertRaises(ValueError, field2required, value)

    def test_field2string_with_string(self):
        from ZPublisher.Converters import field2string
        to_convert = 'to_convert'
        self.assertEqual(field2string(to_convert), to_convert)

    def test_field2bytes_with_bytes(self):
        from ZPublisher.Converters import field2bytes
        to_convert = b'to_convert'
        self.assertEqual(field2bytes(to_convert), to_convert)

    def test_field2bytes_with_text(self):
        from ZPublisher.Converters import field2bytes
        to_convert = 'to_convert'
        expected = b'to_convert'
        self.assertEqual(field2bytes(to_convert), expected)

    def test_field2bytes_with_filelike_object(self):
        from ZPublisher.Converters import field2bytes
        to_convert = b'to_convert'

        class Filelike:
            def read(self):
                return to_convert
        self.assertEqual(field2bytes(Filelike()), to_convert)

    def test_field2date_international_with_proper_date_string(self):
        from ZPublisher.Converters import field2date_international
        to_convert = "2.1.2019"
        from DateTime import DateTime
        expected = DateTime(2019, 1, 2)
        self.assertEqual(field2date_international(to_convert), expected)

    def test_field2lines_with_list(self):
        from ZPublisher.Converters import field2lines
        to_convert = ['one', b'two']
        expected = ['one', 'two']
        self.assertEqual(field2lines(to_convert), expected)

    def test_field2lines_with_tuple(self):
        from ZPublisher.Converters import field2lines
        to_convert = ('one', b'two')
        expected = ['one', 'two']
        self.assertEqual(field2lines(to_convert), expected)

    def test_field2lines_with_empty_string(self):
        from ZPublisher.Converters import field2lines
        to_convert = ''
        self.assertEqual(field2lines(to_convert), [])

    def test_field2lines_with_string_no_newlines(self):
        from ZPublisher.Converters import field2lines
        to_convert = 'abc def ghi'
        expected = ['abc def ghi']
        self.assertEqual(field2lines(to_convert), expected)

    def test_field2lines_with_string_with_newlines(self):
        from ZPublisher.Converters import field2lines
        to_convert = 'abc\ndef\nghi'
        expected = ['abc', 'def', 'ghi']
        self.assertEqual(field2lines(to_convert), expected)

    def test_field2text_with_string_with_newlines(self):
        from ZPublisher.Converters import field2text
        to_convert = 'abc\r\ndef\r\nghi'
        expected = 'abc\ndef\nghi'
        self.assertEqual(field2text(to_convert), expected)

    def test_field2ulines_with_list(self):
        from ZPublisher.Converters import field2ulines
        to_convert = ['one', 'two']
        # unicode converters will go away with Zope 6
        # ignore deprecation warning for test run
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.assertEqual(field2ulines(to_convert),
                             [str(x) for x in to_convert])

    def test_field2ulines_with_tuple(self):
        from ZPublisher.Converters import field2ulines
        to_convert = ('one', 'two')
        # unicode converters will go away with Zope 6
        # ignore deprecation warning for test run
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.assertEqual(field2ulines(to_convert),
                             [str(x) for x in to_convert])

    def test_field2ulines_with_empty_string(self):
        from ZPublisher.Converters import field2ulines
        to_convert = ''
        # unicode converters will go away with Zope 6
        # ignore deprecation warning for test run
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.assertEqual(field2ulines(to_convert), [])

    def test_field2ulines_with_string_no_newlines(self):
        from ZPublisher.Converters import field2ulines
        to_convert = 'abc def ghi'
        # unicode converters will go away with Zope 6
        # ignore deprecation warning for test run
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.assertEqual(field2ulines(to_convert), [to_convert])

    def test_field2ulines_with_string_with_newlines(self):
        from ZPublisher.Converters import field2ulines
        to_convert = 'abc\ndef\nghi'
        # unicode converters will go away with Zope 6
        # ignore deprecation warning for test run
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.assertEqual(field2ulines(to_convert), to_convert.splitlines())

    def test_field2json_with_valid_json(self):
        from ZPublisher.Converters import field2json
        to_convert = '{"key1":"value1","key2": 2,"key3": ["1", "2"]}'
        self.assertEqual(field2json(to_convert),
                         {"key1": "value1", "key2": 2, "key3": ["1", "2"]})

    def test_field2json_with_invalid_json(self):
        from ZPublisher.Converters import field2json
        to_convert = '{"key1":"value1","key2":'
        self.assertRaises(ValueError, field2json, to_convert)
