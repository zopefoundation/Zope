import os
import shutil
import sys
import tempfile
import unittest
from six import StringIO

zope_conf_template = """
%define INSTANCE {}

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


if __name__ == '__main__':
    app.foo = '42'
    print(app.foo)
    print(sys.argv[1:])
"""


class ZConsoleTestCase(unittest.TestCase):

    def setUp(self):
        self.instancedir = tempfile.mkdtemp(prefix='instance')
        self.zopeconf = os.path.join(self.instancedir, 'zope.conf')
        self.stored_sys_argv = sys.argv
        self.stored_stdout = sys.stdout
        with open(self.zopeconf, 'w') as conffile:
            conffile.write(zope_conf_template.format(self.instancedir))

    def tearDown(self):
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
        with open(script, 'w') as scriptfile:
            scriptfile.write(test_script)
        try:
            from Zope2.utilities.zconsole import runscript
            sys.argv = [
                sys.executable,
                'run',
                self.zopeconf,
                script,

                'bar', 'baz']
            sys.stdout = StringIO()
            runscript(self.zopeconf, script, 'bar', 'baz')
            sys.stdout.seek(0)
            got = sys.stdout.read()
        finally:
            sys.argv = self.stored_sys_argv
            sys.stdout = self.stored_stdout
        expected = "42\n['run', '{}', '{}', 'bar', 'baz']\n".format(self.zopeconf, script)  # noqa: E501
        self.assertEqual(expected, got)
