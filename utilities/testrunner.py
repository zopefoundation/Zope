"""testrunner - a Zope test suite utility.

The testrunner utility is used to execute PyUnit test suites. You can find
more information on PyUnit at http://pyunit.sourceforge.net. This utility
should be run from the root of your Zope installation. It will set up the
correct python path environment based on your installation directory so that
test suites can import Zope modules in a way that is fairly independent of
the location of the test suite. It does *not* import the Zope package, so
a test thats depend on dynamic aspects of the Zope environment (such as
SOFTWARE_HOME being defined) may need to 'import Zope' as a part of the
test suite.

Testrunner will look for and execute test suites that follow some simple
conventions. Test modules should have a name prefixed with 'test', such as
'testMyModule.py', and test modules are expected to define a module function
named 'test_suite' that returns a PyUnit TestSuite object. By convention,
we put test suites in 'tests' subdirectories of the packages they test.

Testrunner is used to run all checked in test suites before (final) releases
are made, and can be used to quickly run a particular suite or all suites in
a particular directory."""

import sys, os, imp, string, getopt, traceback
import unittest

VERBOSE = 2

class TestRunner:
    """Test suite runner"""

    def __init__(self, basepath, verbosity=VERBOSE):
        # initialize python path
        self.basepath=path=basepath
        self.verbosity = verbosity
        pjoin=os.path.join
        if sys.platform == 'win32':
            sys.path.insert(0, pjoin(path, 'lib/python'))
            sys.path.insert(1, pjoin(path, 'bin/lib'))
            sys.path.insert(2, pjoin(path, 'bin/lib/plat-win'))
            sys.path.insert(3, pjoin(path, 'bin/lib/win32'))
            sys.path.insert(4, pjoin(path, 'bin/lib/win32/lib'))
            sys.path.insert(5, path)
        else:
            sys.path.insert(0, pjoin(path, 'lib/python'))
            sys.path.insert(1, path)

    def getSuiteFromFile(self, filepath):
        if not os.path.isfile(filepath):
            raise ValueError, '%s is not a file' % filepath
        path, filename=os.path.split(filepath)
        name, ext=os.path.splitext(filename)
        file, pathname, desc=imp.find_module(name, [path])
        # Add path of imported module to sys.path, so local imports work.
        sys.path.insert(0, path)
        try:     module=imp.load_module(name, file, pathname, desc)
        finally: file.close()
        # Remove extra path again.
        sys.path.remove(path)
        function=getattr(module, 'test_suite', None)
        if function is None:
            return None
        return function()

    def smellsLikeATest(self, filepath, find=string.find):
        path, name = os.path.split(filepath)
        fname, ext = os.path.splitext(name)
        
        if name[:4]=='test' and name[-3:]=='.py' and \
           name != 'testrunner.py':
            
            file=open(filepath, 'r')
            lines=file.readlines()
            file.close()
            for line in lines:
                if (find(line, 'def test_suite(') > -1) or \
                   (find(line, 'framework(') > -1):
                    return 1
        return 0

    def runSuite(self, suite):
        runner=unittest.TextTestRunner(verbosity=self.verbosity)
        runner.run(suite)

    def report(self, message):
        print message
        print

    def runAllTests(self):
        """Run all tests found in the current working directory and
           all subdirectories."""
        self.runPath(self.basepath)

    def runPath(self, pathname):
        """Run all tests found in the directory named by pathname
           and all subdirectories."""
        if not os.path.isabs(pathname):
            pathname = os.path.join(self.basepath, pathname)
        names=os.listdir(pathname)
        for name in names:
            fullpath=os.path.join(pathname, name)
            if os.path.isdir(fullpath):
                self.runPath(fullpath)
            elif self.smellsLikeATest(fullpath):
                self.runFile(fullpath)

    def runFile(self, filename):
        """Run the test suite defined by filename."""
        working_dir = os.getcwd()
        dirname, name = os.path.split(filename)
        if dirname:
            os.chdir(dirname)
        self.report('Running: %s' % filename)
        try:    suite=self.getSuiteFromFile(name)
        except:
            traceback.print_exc()
            suite=None            
        if suite is not None:
            self.runSuite(suite)
        else:
            self.report('No test suite found in file:\n%s\n' % filename)
        os.chdir(working_dir)


def main(args):

    usage_msg="""Usage: python testrunner.py options

    If run without options, testrunner will display this usage
    message. If you want to run all test suites found in all
    subdirectories of the current working directory, use the
    -a option.

    options:

       -a

          Run all tests found in all subdirectories of the current
          working directory. This is the default if no options are
          specified.

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

       -h

          Display usage information.
    """

    pathname=None
    filename=None
    test_all=None
    verbosity = VERBOSE

    options, arg=getopt.getopt(args, 'ahd:f:v:q')
    if not options:
        err_exit(usage_msg)
    for name, value in options:
        name=name[1:]
        if name == 'a':
            test_all=1
        elif name == 'd':
            pathname=string.strip(value)
        elif name == 'f':
            filename=string.strip(value)
        elif name == 'h':
            err_exit(usage_msg, 0)
        elif name == 'v':
            verbosity = int(value)
        elif name == 'q':
            verbosity = 1
        else:
            err_exit(usage_msg)

    testrunner = TestRunner(os.getcwd(), verbosity=verbosity)
    if test_all:
        testrunner.runAllTests()
    elif pathname:
        testrunner.runPath(pathname)
    elif filename:
        testrunner.runFile(filename)
    sys.exit(0)


def err_exit(message, rc=2):
    sys.stderr.write("\n%s\n" % message)
    sys.exit(rc)


if __name__ == '__main__':
    main(sys.argv[1:])
