import os
import shutil
import sys
import tempfile
import unittest
from io import StringIO

from App.config import getConfiguration
from App.config import setConfiguration


zope_conf_template = """
%define INSTANCE {0}

instancehome $INSTANCE

<zodb_db main>
   <filestorage>
     path $INSTANCE/Data.fs
   </filestorage>
   mount-point /
</zodb_db>
"""

test_script = """
import sys
import OFS.PropertyManager



def print_info():
    # This tests the availability of global variables and imports.
    print(sys.argv[1:])
    # 'PropertyManager'
    print(OFS.PropertyManager.PropertyManager.__name__)

if __name__ == '__main__':
    app.foo = '42'
    print(app.foo)
    print_info()
"""


class ZConsoleTestCase(unittest.TestCase):

    def setUp(self):
        self.instancedir = tempfile.mkdtemp(prefix='foo42-')
        self.zopeconf = os.path.join(self.instancedir, 'zope.conf')
        self.stored_sys_argv = sys.argv
        self.stored_stdout = sys.stdout
        self.stored_app_config = getConfiguration()
        with open(self.zopeconf, 'w') as conffile:
            conffile.write(zope_conf_template.format(self.instancedir))

    def tearDown(self):
        setConfiguration(self.stored_app_config)
        shutil.rmtree(self.instancedir)

    def test_debug(self):
        try:
            from Zope2.utilities.zconsole import debug
            sys.stdout = StringIO()
            got = debug(self.zopeconf)
            expected = '<Application at >'
        finally:
            sys.argv = self.stored_sys_argv
            sys.stdout = self.stored_stdout
        self.assertEqual(expected, str(got))

    def test_runscript(self):
        script = os.path.join(self.instancedir, 'test_script.py')
        # Use a backslash to fake windows paths under linux
        bar = r'\bar'
        with open(script, 'w') as scriptfile:
            scriptfile.write(test_script)
        try:
            from Zope2.utilities.zconsole import runscript
            sys.argv = [
                sys.executable,
                'run',
                self.zopeconf,
                script,
                bar, 'baz']
            sys.stdout = StringIO()
            runscript(self.zopeconf, script, 'bar', 'baz')
            sys.stdout.seek(0)
            got = sys.stdout.read()
        finally:
            sys.argv = self.stored_sys_argv
            sys.stdout = self.stored_stdout
        # We get double escape for backslash \ on windows from test script,
        # so we have the raw string in there.
        expected = (
            "42\n"
            rf"['run', {self.zopeconf!r}, {script!r}, {bar!r}, 'baz']"
            "\nPropertyManager\n")
        self.assertEqual(expected, got)
