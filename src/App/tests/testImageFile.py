import io
import os.path
import unittest
from io import BytesIO

import App
from Testing.ZopeTestCase.warnhook import WarningsHook
from ZPublisher.HTTPRequest import WSGIRequest
from ZPublisher.HTTPResponse import WSGIResponse


class TestImageFile(unittest.TestCase):

    def setUp(self):
        # ugly: need to save the old App.config configuration value since
        # ImageFile might read it and trigger setting it to the default value
        self.oldcfg = App.config._config
        self.warningshook = WarningsHook()
        self.warningshook.install()

    def tearDown(self):
        self.warningshook.uninstall()
        # ugly: need to restore configuration, or lack thereof
        App.config._config = self.oldcfg

    def test_warn_on_software_home_default(self):
        App.ImageFile.ImageFile('App/www/zopelogo.png')
        self.assertEqual(self.warningshook.warnings.pop()[0],
                         App.ImageFile.NON_PREFIX_WARNING)

    def test_no_warn_on_absolute_path(self):
        path = os.path.join(os.path.dirname(App.__file__),
                            'www', 'zopelogo.png')
        App.ImageFile.ImageFile(path)
        self.assertFalse(self.warningshook.warnings)

    def test_no_warn_on_path_as_prefix(self):
        prefix = os.path.dirname(App.__file__)
        App.ImageFile.ImageFile('www/zopelogo.png', prefix)
        self.assertFalse(self.warningshook.warnings)

    def test_no_warn_on_namespace_as_prefix(self):
        # same as calling globals() inside the App module
        prefix = App.__dict__
        App.ImageFile.ImageFile('www/zopelogo.png', prefix)
        self.assertFalse(self.warningshook.warnings)


class TestImageFileFunctional(unittest.TestCase):

    def test_index_html(self):
        env = {
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'REQUEST_METHOD': 'GET',
        }
        stdin = BytesIO()
        stdout = BytesIO()
        response = WSGIResponse(stdout)
        request = WSGIRequest(stdin, env, response)
        path = os.path.join(os.path.dirname(App.__file__),
                            'www', 'zopelogo.png')
        image = App.ImageFile.ImageFile(path)
        result = image.index_html(request, response)
        self.assertEqual(stdout.getvalue(), b'')
        self.assertIsInstance(result, io.FileIO)
        self.assertTrue(b''.join(result).startswith(b'\x89PNG\r\n'))
        self.assertEqual(len(result), image.size)
        self.assertEqual(response.getHeader('Content-Length'), str(image.size))
        result.close()

    def test_304(self):
        env = {
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'REQUEST_METHOD': 'GET',
            'IF_MODIFIED_SINCE': '2050/12/31',
        }
        stdout = BytesIO()
        response = WSGIResponse(stdout)
        request = WSGIRequest(BytesIO(), env, response)
        path = os.path.join(os.path.dirname(App.__file__),
                            'www', 'zopelogo.png')
        image = App.ImageFile.ImageFile(path)
        result = image.index_html(request, response)
        self.assertEqual(stdout.getvalue(), b'')
        self.assertEqual(len(result), 0)
        self.assertEqual(response.getHeader('Content-Length'), '0')

    def test__str__returns_native_string(self):
        path = os.path.join(os.path.dirname(App.__file__),
                            'www', 'zopelogo.png')
        image = App.ImageFile.ImageFile(path)
        self.assertIsInstance(str(image), str)
