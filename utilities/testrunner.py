#! /usr/bin/env python2.2
"""testrunner - a Zope test suite utility.

The testrunner utility is used to execute PyUnit test suites. This utility
should be run from the root of your Zope source directory. It will set up the
correct python path environment based on your source directory so that
test suites can import Zope modules in a way that is fairly independent of
the location of the test suite. It does *not* import the Zope package, so
a test thats depend on dynamic aspects of the Zope environment (such as
SOFTWARE_HOME being defined) may need to 'import Zope' as a part of the
test suite.

Testrunner will look for and execute test suites that follow some simple
conventions. Test modules should have a name prefixed with 'test', such as
'testMyModule.py', and test modules are expected to define a module function
named 'test_suite' that returns a TestSuite object. By convention,
we put test modules in a 'tests' sub-package of the package they test.

Testrunner is used to run all checked in test suites before (final) releases
are made, and can be used to quickly run a particular suite or all suites in
a particular directory."""

import getopt
import imp
import os
import sys
import time
import traceback
import unittest

VERBOSE = 2

class TestRunner:
    """Test suite runner"""

    def __init__(self, path, verbosity, mega_suite):
        self.basepath = path
        self.verbosity = verbosity
        self.results = []
        self.mega_suite = mega_suite
        # initialize python path
        pjoin = os.path.join
        if sys.platform == 'win32':
            newpaths = [pjoin(path, 'lib', 'python'),
                        pjoin(path, 'bin', 'lib'),
                        pjoin(path, 'bin', 'lib', 'plat-win'),
                        pjoin(path, 'bin', 'lib', 'win32'),
                        pjoin(path, 'bin', 'lib', 'win32', 'lib'),
                        path]
        else:
            newpaths = [pjoin(path, 'lib', 'python'),
                        path]
        sys.path[:0] = newpaths

    def getSuiteFromFile(self, filepath):
        if not os.path.isfile(filepath):
            raise ValueError, '%s is not a file' % filepath
        path, filename = os.path.split(filepath)
        name, ext = os.path.splitext(filename)
        file, pathname, desc = imp.find_module(name, [path])
        saved_syspath = sys.path[:]
        module = None
        try:
            sys.path.append(path)       # let module find things in its dir
            try:
                module=imp.load_module(name, file, pathname, desc)
            except KeyboardInterrupt:
                raise
            except:
                (tb_t, tb_v, tb_tb) = sys.exc_info()
                self.report("Module %s failed to load\n%s: %s" % (pathname,
                        tb_t, tb_v))
                self.report(''.join(traceback.format_tb(tb_tb)) + '\n')
                del tb_tb
        finally:
            file.close()
            sys.path.pop()              # Remove module level path
            sys.path[:] = saved_syspath
        function=getattr(module, 'test_suite', None)
        if function is None:
            return None
        return function()

    def smellsLikeATest(self, filepath):
        path, name = os.path.split(filepath)
        fname, ext = os.path.splitext(name)

        if (  name[:4] == 'test'
              and name[-3:] == '.py'
              and name != 'testrunner.py'):
            file = open(filepath, 'r')
            lines = file.readlines()
            file.close()
            for line in lines:
                if (line.find('def test_suite(') > -1) or \
                   (line.find('framework(') > -1):
                    return True
        return False

    def runSuite(self, suite):
        if suite:
            runner = self.getTestRunner()
            self.results.append(runner.run(suite))
        else:
            self.report('No suitable tests found')

    _runner = None

    def getTestRunner(self):
        if self._runner is None:
            self._runner = self.createTestRunner()
        return self._runner

    def createTestRunner(self):
        return unittest.TextTestRunner(stream=sys.stderr,
                                       verbosity=self.verbosity)

    def report(self, message):
        print >>sys.stderr, message

    def runAllTests(self):
        """Run all tests found in the current working directory and
           all subdirectories."""
        self.runPath(self.basepath)

    def listTestableNames(self, pathname):
        """Return a list of the names to be traversed to build tests."""
        names = os.listdir(pathname)
        if "build" in names:
            # Don't recurse into build directories created by setup.py
            names.remove("build")
        if '.testinfo' in names:  # allow local control
            f = open(os.path.join(pathname, '.testinfo'))
            lines = filter(None, f.readlines())
            lines = map(lambda x: x[-1]=='\n' and x[:-1] or x, lines)
            names = filter(lambda x: x and x[0] != '#', lines)
            f.close()
        return names

    def extractSuite(self, pathname):
        """Extract and return the appropriate test suite."""
        if os.path.isdir(pathname):
            suite = unittest.TestSuite()
            for name in self.listTestableNames(pathname):
                fullpath = os.path.join(pathname, name)
                sub_suite = self.extractSuite(fullpath)
                if sub_suite:
                    suite.addTest(sub_suite)
            return suite.countTestCases() and suite or None

        elif self.smellsLikeATest(pathname):
            dirname, name = os.path.split(pathname)
            working_dir = os.getcwd()
            try:
                if dirname:
                    os.chdir(dirname)
                try:
                    suite = self.getSuiteFromFile(name)
                except KeyboardInterrupt:
                    raise
                except:
                    self.report('No test suite found in file:\n%s\n'
                                % pathname)
                    if self.verbosity > 1:
                        traceback.print_exc()
                    suite = None
            finally:
                os.chdir(working_dir)
            return suite

        else:
            # no test there!
            return None

    def runPath(self, pathname):
        """Run all tests found in the directory named by pathname
           and all subdirectories."""
        if not os.path.isabs(pathname):
            pathname = os.path.join(self.basepath, pathname)

        if self.mega_suite:
            suite = self.extractSuite(pathname)
            self.runSuite(suite)
        else:
            for name in self.listTestableNames(pathname):
                fullpath = os.path.join(pathname, name)
                if os.path.isdir(fullpath):
                    self.runPath(fullpath)
                elif self.smellsLikeATest(fullpath):
                    self.runFile(fullpath)

    def runFile(self, filename):
        """Run the test suite defined by filename."""
        working_dir = os.getcwd()
        dirname, name = os.path.split(filename)
        if dirname:
            if self.verbosity > 2:
                print >>sys.stderr, '*** Changing directory to:', dirname
            os.chdir(dirname)
        self.report('Running: %s' % filename)
        try:
            suite = self.getSuiteFromFile(name)
        except KeyboardInterrupt:
            raise
        except:
            traceback.print_exc()
            suite = None
        if suite is not None:
            self.runSuite(suite)
        else:
            self.report('No test suite found in file:\n%s\n' % filename)
        if self.verbosity > 2:
            print >>sys.stderr, '*** Restoring directory to:', working_dir
        os.chdir(working_dir)


class TimingTestResult(unittest._TextTestResult):
    def __init__(self, *args, **kw):
        self.timings = []
        unittest._TextTestResult.__init__(self, *args, **kw)

    def startTest(self, test):
        unittest._TextTestResult.startTest(self, test)
        self._t2 = None
        self._t1 = time.time()

    def stopTest(self, test):
        t2 = time.time()
        if self._t2 is not None:
            t2 = self._t2
        t = t2 - self._t1
        self.timings.append((t, str(test)))
        unittest._TextTestResult.stopTest(self, test)

    def addSuccess(self, test):
        self._t2 = time.time()
        unittest._TextTestResult.addSuccess(self, test)

    def addError(self, test, err):
        self._t2 = time.time()
        unittest._TextTestResult.addError(self, test, err)

    def addFailure(self, test, err):
        self._t2 = time.time()
        unittest._TextTestResult.addFailure(self, test, err)


class TimingTestRunner(unittest.TextTestRunner):
    def __init__(self, *args, **kw):
        unittest.TextTestRunner.__init__(self, *args, **kw)
        self.timings = []

    def _makeResult(self):
        r = TimingTestResult(self.stream, self.descriptions, self.verbosity)
        self.timings = r.timings
        return r


class TestTimer(TestRunner):
    def createTestRunner(self):
        return TimingTestRunner(stream=sys.stderr,
                                verbosity=self.verbosity)

    def reportTimes(self, num):
        r = self.getTestRunner()
        r.timings.sort()
        for item in r.timings[-num:]:
            print "%.1f %s" % item


def remove_stale_bytecode(arg, dirname, names):
    names = map(os.path.normcase, names)
    for name in names:
        if name.endswith(".pyc") or name.endswith(".pyo"):
            srcname = name[:-1]
            if srcname not in names:
                fullname = os.path.join(dirname, name)
                print "Removing stale bytecode file", fullname
                os.unlink(fullname)

def main(args):
    usage_msg = """Usage: python testrunner.py options

    If run without options, testrunner will display this usage
    message. If you want to run all test suites found in all
    subdirectories of the current working directory, use the
    -a option.

    options:

       -a
          Run all tests found in all subdirectories of the current
          working directory.

       -m
          Run all tests in a single, giant suite (consolidates error
          reporting). [default]

       -M
          Run each test file's suite separately (noisier output, may
          help in isolating global effects later).

       -p
          Add 'lib/python' to the Python search path. [default]

       -P
          *Don't* add 'lib/python' to the Python search path.

       -d dirpath
          Run all tests found in the directory specified by dirpath,
          and recursively in all its subdirectories. The dirpath
          should be a full system path.

       -f filepath
          Run the test suite found in the file specified. The filepath
          should be a fully qualified path to the file to be run.

       -v level
          Set the Verbosity level to level.  Newer versions of
          unittest.py allow more options than older ones.  Allowed
          values are:

            0 - Silent
            1 - Quiet (produces a dot for each succesful test)
            2 - Verbose (default - produces a line of output for each test)

       -q
          Run tests without producing verbose output.  The tests are
          normally run in verbose mode, which produces a line of
          output for each test that includes the name of the test and
          whether it succeeded.  Running with -q is the same as
          running with -v1.

       -o filename
          Output test results to the specified file rather than
          to stderr.

       -t N
          Report time taken by the most expensive N tests.

       -h
          Display usage information.
    """

    pathname = None
    filename = None
    test_all = False
    verbosity = VERBOSE
    mega_suite = True
    set_python_path = True
    timed = 0

    options, arg = getopt.getopt(args, 'amPhd:f:v:qMo:t:')
    if not options:
        err_exit(usage_msg)
    for name, value in options:
        if name == '-a':
            test_all = True
        elif name == '-m':
            mega_suite = True
        elif name == '-M':
            mega_suite = False
        elif name == '-p':
            set_python_path = True
        elif name == '-P':
            set_python_path = False
        elif name == '-d':
            pathname = value.strip()
        elif name == '-f':
            filename = value.strip()
        elif name == '-h':
            err_exit(usage_msg, 0)
        elif name == '-v':
            verbosity = int(value)
        elif name == '-q':
            verbosity = 1
        elif name == '-t':
            timed = int(value)
            assert timed >= 0
        elif name == '-o':
            f = open(value, 'w')
            sys.stderr = f
        else:
            err_exit(usage_msg)

    os.path.walk(os.curdir, remove_stale_bytecode, None)

    if timed:
        testrunner = TestTimer(os.getcwd(), verbosity, mega_suite)
    else:
        testrunner = TestRunner(os.getcwd(), verbosity, mega_suite)

    if set_python_path:
        script = sys.argv[0]
        script_dir = os.path.dirname(os.path.abspath(script))
        zope_dir = os.path.dirname(script_dir)
        sw_home = os.path.join(zope_dir, 'lib', 'python')
        if verbosity > 1:
            testrunner.report("Adding %s to sys.path." % sw_home)
        sys.path.insert(0, sw_home)
        os.environ['SOFTWARE_HOME'] = sw_home

    try:
        # Try to set up the testing environment (esp. INSTANCE_HOME,
        # so we use the right custom_zodb.py.)
        import Testing
    except ImportError:
        pass

    if test_all:
        testrunner.runAllTests()
    elif pathname:
        testrunner.runPath(pathname)
    elif filename:
        testrunner.runFile(filename)

    if timed:
        testrunner.reportTimes(timed)

    ## Report overall errors / failures if there were any
    fails = reduce(lambda x, y: x + len(y.failures), testrunner.results, 0)
    errs  = reduce(lambda x, y: x + len(y.errors), testrunner.results, 0)
    if fails or errs:
        msg = '=' * 70
        msg += "\nOVERALL FAILED ("
        if fails:
            msg += "total failures=%d" % fails
        if errs:
            if fails:
                msg += ", "
            msg += "total errors=%d" % errs
        msg += ")"
        err_exit(msg, 1)

    sys.exit(0)


def err_exit(message, rc=2):
    sys.stderr.write("\n%s\n" % message)
    sys.exit(rc)


if __name__ == '__main__':
    main(sys.argv[1:])
