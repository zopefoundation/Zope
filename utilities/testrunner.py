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

    def __init__(self, basepath, verbosity=VERBOSE, results=[], mega_suite=0):
        # initialize python path
        self.basepath=path=basepath
        self.verbosity = verbosity
        self.results = results
        self.mega_suite = mega_suite
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
        saved_syspath = sys.path[:]
        try:
            sys.path.append(path)       # let module find things in its dir
            module=imp.load_module(name, file, pathname, desc)
        finally:
            file.close()
            sys.path.pop()              # Remove module level path
            sys.path[:] = saved_syspath
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
        self.results.append(runner.run(suite))

    def report(self, message):
        sys.stderr.write( '%s\n' % message )

    def runAllTests(self):
        """Run all tests found in the current working directory and
           all subdirectories."""
        self.runPath(self.basepath)

    def listTestableNames( self, pathname ):
        """
            Return a list of the names to be traversed to build tests.
        """
        names = os.listdir(pathname)
        if '.testinfo' in names:  # allow local control
            f = open( os.path.join( pathname, '.testinfo' ) )
            lines = filter( None, f.readlines() )
            lines = map( lambda x: x[-1]=='\n' and x[:-1] or x, lines )
            names = filter( lambda x: x and x[0] != '#', lines )
            f.close()
        return names

    def extractSuite( self, pathname ):
        """
            Extract and return the appropriate test suite.
        """
        if os.path.isdir( pathname ):

            suite = unittest.TestSuite()

            for name in self.listTestableNames( pathname ):

                fullpath = os.path.join( pathname, name )
                sub_suite = self.extractSuite( fullpath )
                if sub_suite:
                    suite.addTest( sub_suite )

            return suite.countTestCases() and suite or None

        elif self.smellsLikeATest( pathname ):

            working_dir = os.getcwd()
            try:
                dirname, name = os.path.split(pathname)
                if dirname:
                    os.chdir(dirname)
                try:
                    suite = self.getSuiteFromFile(name)
                except:
                    self.report('No test suite found in file:\n%s\n' % pathname)
                    if self.verbosity > 1:
                        traceback.print_exc()
                    suite = None            
            finally:
                os.chdir(working_dir)
            
            return suite

        else: # no test there!

            return None

    def runPath(self, pathname):
        """Run all tests found in the directory named by pathname
           and all subdirectories."""
        if not os.path.isabs(pathname):
            pathname = os.path.join(self.basepath, pathname)

        if self.mega_suite:
            suite = self.extractSuite( pathname )
            self.runSuite( suite )
        else:
            for name in self.listTestableNames(pathname):
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
            if self.verbosity > 2:
                sys.stderr.write( '*** Changing directory to: %s\n' % dirname )
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
        if self.verbosity > 2:
            sys.stderr.write( '*** Restoring directory to: %s\n' % working_dir )
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

       -h

          Display usage information.
    """

    pathname=None
    filename=None
    test_all=None
    verbosity = VERBOSE
    mega_suite = 1
    set_python_path = 1

    options, arg=getopt.getopt(args, 'amPhd:f:v:qM')
    if not options:
        err_exit(usage_msg)
    for name, value in options:
        name=name[1:]
        if name == 'a':
            test_all=1
        elif name == 'm':
            mega_suite = 1
        elif name == 'M':
            mega_suite = 0
        elif name == 'p':
            set_python_path = 1
        elif name == 'P':
            set_python_path = 0
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

    testrunner = TestRunner( os.getcwd()
                           , verbosity=verbosity
                           , mega_suite=mega_suite)

    if set_python_path:
        script = sys.argv[0]
        script_dir = os.path.split( os.path.abspath( script ) )[0]
        zope_dir = os.path.abspath( os.path.join( script_dir, '..' ) )
        sw_home = os.path.join( zope_dir, 'lib', 'python' )
        if verbosity > 1:
            testrunner.report( "Adding %s to sys.path." % sw_home )
        sys.path.insert( 0, sw_home )
        os.environ['SOFTWARE_HOME'] = sw_home

    if test_all:
        testrunner.runAllTests()
    elif pathname:
        testrunner.runPath(pathname)
    elif filename:
        testrunner.runFile(filename)


    ## Report overall errors / failures if there were any
    fails = reduce(lambda x, y: x + len(y.failures), testrunner.results, 0)
    errs  = reduce(lambda x, y: x + len(y.errors), testrunner.results, 0)
    if fails or errs:
        msg = '=' * 70
        msg += "\nOVERALL FAILED ("
        if fails:
            msg += "total failures=%d" % fails
        if errs:
            if fails: msg += ", "
            msg += "total errors=%d" % errs
        msg += ")"
        err_exit(msg, 1)
        
    sys.exit(0)


def err_exit(message, rc=2):
    sys.stderr.write("\n%s\n" % message)
    sys.exit(rc)


if __name__ == '__main__':
    main(sys.argv[1:])
