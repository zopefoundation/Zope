import unittest
import os.path
import App
from Testing.ZopeTestCase.warnhook import WarningsHook


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
        App.ImageFile.ImageFile('App/www/zopelogo.jpg')
        self.assertEquals(self.warningshook.warnings.pop()[0],
                          App.ImageFile.NON_PREFIX_WARNING)

    def test_no_warn_on_absolute_path(self):
        path = os.path.join(os.path.dirname(App.__file__),
                            'www','zopelogo.jpg')
        App.ImageFile.ImageFile(path)
        self.assertFalse(self.warningshook.warnings)

    def test_no_warn_on_path_as_prefix(self):
        prefix = os.path.dirname(App.__file__)
        App.ImageFile.ImageFile('www/zopelogo.jpg', prefix)
        self.assertFalse(self.warningshook.warnings)

    def test_no_warn_on_namespace_as_prefix(self):
        prefix = App.__dict__ # same as calling globals() inside the App module
        App.ImageFile.ImageFile('www/zopelogo.jpg', prefix)
        self.assertFalse(self.warningshook.warnings)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestImageFile),
        ))
