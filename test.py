#!/usr/bin/env python2.3

##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
test.py [-abcdDfgGhLmprtTuv] [modfilter [testfilter]]

Find and run tests written using the unittest module.

The test runner searches for Python modules that contain test suites.
It collects those suites, and runs the tests.  There are many options
for controlling how the tests are run.  There are options for using
the debugger, reporting code coverage, and checking for refcount problems.

The test runner uses the following rules for finding tests to run.  It
searches for packages and modules that contain "tests" as a component
of the name, e.g. "frob.tests.nitz" matches this rule because tests is
a sub-package of frob.  Within each "tests" package, it looks for
modules that begin with the name "test."  For each test module, it
imports the module and calls the test_suite() method, which must
return a unittest TestSuite object.  (If a package contains a file
named .testinfo, it will not be searched for tests.  Really.)

-a level
--all
    Run the tests at the given level.  Any test at a level at or below
    this is run, any test at a level above this is not run.  Level 0
    runs all tests.  The default is to run tests at level 1.  --all is
    a shortcut for -a 0.

-b
    Run "python setup.py build_ext -i" before running tests, where
    "python" is the version of python used to run test.py.  Highly
    recommended.  Tests will be run from the build directory.  (Note:
    In Python < 2.3 the -q flag is added to the setup.py command
    line.)

-c  use pychecker

-d
    Instead of the normal test harness, run a debug version which
    doesn't catch any exceptions.  This is occasionally handy when the
    unittest code catching the exception doesn't work right.
    Unfortunately, the debug harness doesn't print the name of the
    test, so Use With Care.

--dir directory 
    Option to limit where tests are searched for. This is
    important when you *really* want to limit the code that gets run.
    For example, if refactoring interfaces, you don't want to see the way
    you have broken setups for tests in other packages. You *just* want to
    run the interface tests.

-D
    Works like -d, except that it loads pdb when an exception occurs.

-f
    Run functional tests instead of unit tests.

-g threshold
    Set the garbage collector generation0 threshold.  This can be used
    to stress memory and gc correctness.  Some crashes are only
    reproducible when the threshold is set to 1 (agressive garbage
    collection).  Do "-g 0" to disable garbage collection altogether.

-G gc_option
    Set the garbage collection debugging flags.  The argument must be one
    of the DEBUG_ flags defined bythe Python gc module.  Multiple options
    can be specified by using "-G OPTION1 -G OPTION2."

--libdir test_root
    Search for tests starting in the specified start directory
    (useful for testing components being developed outside the main
    "src" or "build" trees).

--keepbytecode
    Do not delete all stale bytecode before running tests

-L
    Keep running the selected tests in a loop.  You may experience
    memory leakage.

-t
    Time the individual tests and print a list of the top 50, sorted from
    longest to shortest.

-p
    Show running progress.  It can be combined with -v or -vv.

-r
    Look for refcount problems.
    This requires that Python was built --with-pydebug.

-T
    Use the trace module from Python for code coverage.  XXX This only
    works if trace.py is explicitly added to PYTHONPATH.  The current
    utility writes coverage files to a directory named `coverage' that
    is parallel to `build'.  It also prints a summary to stdout.

-v
    Verbose output.  With one -v, unittest prints a dot (".") for each
    test run.  With -vv, unittest prints the name of each test (for
    some definition of "name" ...).  With no -v, unittest is silent
    until the end of the run, except when errors occur.

-u
-m
    Use the PyUnit GUI instead of output to the command line.  The GUI
    imports tests on its own, taking care to reload all dependencies
    on each run.  The debug (-d), verbose (-v), and Loop (-L) options
    will be ignored.  The testfilter filter is also not applied.

    -m starts the gui minimized.  Double-clicking the progress bar
    will start the import and run all tests.


modfilter
testfilter
    Case-sensitive regexps to limit which tests are run, used in search
    (not match) mode.
    In an extension of Python regexp notation, a leading "!" is stripped
    and causes the sense of the remaining regexp to be negated (so "!bc"
    matches any string that does not match "bc", and vice versa).
    By default these act like ".", i.e. nothing is excluded.

    modfilter is applied to a test file's path, starting at "build" and
    including (OS-dependent) path separators.

    testfilter is applied to the (method) name of the unittest methods
    contained in the test files whose paths modfilter matched.

Extreme (yet useful) examples:

    test.py -vvb . "^checkWriteClient$"

    Builds the project silently, then runs unittest in verbose mode on all
    tests whose names are precisely "checkWriteClient".  Useful when
    debugging a specific test.

    test.py -vvb . "!^checkWriteClient$"

    As before, but runs all tests whose names aren't precisely
    "checkWriteClient".  Useful to avoid a specific failing test you don't
    want to deal with just yet.

    test.py -m . "!^checkWriteClient$"

    As before, but now opens up a minimized PyUnit GUI window (only showing
    the progress bar).  Useful for refactoring runs where you continually want
    to make sure all tests still pass.
"""

import gc
import os
import re
import pdb
import sys
import time
import traceback
import unittest

from distutils.util import get_platform

PLAT_SPEC = "%s-%s" % (get_platform(), sys.version[0:3])

def callers(n):
    callers = []
    f = sys._getframe(2)
    while f:
        co = f.f_code
        callers.append((co.co_filename, co.co_name))
        f = f.f_back
        n -= 1
        if not n:
            break
    return callers

class ImmediateTestResult(unittest._TextTestResult):

    __super_init = unittest._TextTestResult.__init__
    __super_startTest = unittest._TextTestResult.startTest
    __super_printErrors = unittest._TextTestResult.printErrors

    def __init__(self, stream, descriptions, verbosity, debug=False,
                 count=None, progress=False):
        self.__super_init(stream, descriptions, verbosity)
        self._debug = debug
        self._progress = progress
        self._progressWithNames = False
        self.count = count
        self._testtimes = {}
        if progress and verbosity == 1:
            self.dots = False
            self._progressWithNames = True
            self._lastWidth = 0
            self._maxWidth = 80
            try:
                import curses
            except ImportError:
                pass
            else:
                import curses.wrapper
                def get_max_width(scr, self=self):
                    self._maxWidth = scr.getmaxyx()[1]
                try:
                    curses.wrapper(get_max_width)
                except curses.error:
                    pass
            self._maxWidth -= len("xxxx/xxxx (xxx.x%): ") + 1

    def stopTest(self, test):
        self._testtimes[test] = time.time() - self._testtimes[test]
        if gc.garbage:
            print "The following test left garbage:"
            print test
            print gc.garbage
            # XXX Perhaps eat the garbage here, so that the garbage isn't
            #     printed for every subsequent test.

    def print_times(self, stream, count=None):
        results = self._testtimes.items()
        results.sort(lambda x, y: cmp(y[1], x[1]))
        if count:
            n = min(count, len(results))
            if n:
                print >>stream, "Top %d longest tests:" % n
        else:
            n = len(results)
        if not n:
            return
        for i in range(n):
            print >>stream, "%6dms" % int(results[i][1] * 1000), results[i][0]

    def _print_traceback(self, msg, err, test, errlist):
        if self.showAll or self.dots or self._progress:
            self.stream.writeln("\n")
            self._lastWidth = 0

        tb = "".join(traceback.format_exception(*err))
        self.stream.writeln(msg)
        self.stream.writeln(tb)
        errlist.append((test, tb))

    def startTest(self, test):
        if self._progress:
            self.stream.write("\r%4d" % (self.testsRun + 1))
            if self.count:
                self.stream.write("/%d (%5.1f%%)" % (self.count,
                                  (self.testsRun + 1) * 100.0 / self.count))
            if self.showAll:
                self.stream.write(": ")
            elif self._progressWithNames:
                # XXX will break with multibyte strings
                name = self.getShortDescription(test)
                width = len(name)
                if width < self._lastWidth:
                    name += " " * (self._lastWidth - width)
                self.stream.write(": %s" % name)
                self._lastWidth = width
            self.stream.flush()
        self.__super_startTest(test)
        self._testtimes[test] = time.time()

    def getShortDescription(self, test):
        s = self.getDescription(test)
        if len(s) > self._maxWidth:
            pos = s.find(" (")
            if pos >= 0:
                w = self._maxWidth - (pos + 5)
                if w < 1:
                    # first portion (test method name) is too long
                    s = s[:self._maxWidth-3] + "..."
                else:
                    pre = s[:pos+2]
                    post = s[-w:]
                    s = "%s...%s" % (pre, post)
        return s[:self._maxWidth]

    def addError(self, test, err):
        if self._progress:
            self.stream.write("\r")
        if self._debug:
            raise err[0], err[1], err[2]
        self._print_traceback("Error in test %s" % test, err,
                              test, self.errors)

    def addFailure(self, test, err):
        if self._progress:
            self.stream.write("\r")
        if self._debug:
            raise err[0], err[1], err[2]
        self._print_traceback("Failure in test %s" % test, err,
                              test, self.failures)

    def printErrors(self):
        if self._progress and not (self.dots or self.showAll):
            self.stream.writeln()
        self.__super_printErrors()

    def printErrorList(self, flavor, errors):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (flavor, self.getDescription(test)))
            self.stream.writeln(self.separator2)
            self.stream.writeln(err)


class ImmediateTestRunner(unittest.TextTestRunner):

    __super_init = unittest.TextTestRunner.__init__

    def __init__(self, **kwarg):
        debug = kwarg.get("debug")
        if debug is not None:
            del kwarg["debug"]
        progress = kwarg.get("progress")
        if progress is not None:
            del kwarg["progress"]
        self.__super_init(**kwarg)
        self._debug = debug
        self._progress = progress
        # Create the test result here, so that we can add errors if
        # the test suite search process has problems.  The count
        # attribute must be set in run(), because we won't know the
        # count until all test suites have been found.
        self.result = ImmediateTestResult(
            self.stream, self.descriptions, self.verbosity, debug=self._debug,
            progress=self._progress)

    def _makeResult(self):
        # Needed base class run method.
        return self.result

    def run(self, test):
        self.result.count = test.countTestCases()
        return unittest.TextTestRunner.run(self, test)

# setup list of directories to put on the path
class PathInit:
    def __init__(self, build, libdir=None):
        # Calculate which directories we're going to add to sys.path, and cd
        # to the appropriate working directory
        org_cwd = os.getcwd()
        self.libdir = "lib/python"
        # Hack sys.path
        self.cwd = os.getcwd()
        sys.path.insert(0, os.path.join(self.cwd, self.libdir))
        # Hack again for external products.
        global functional
        kind = functional and "functional" or "unit"
        if libdir:
            extra = os.path.join(org_cwd, libdir)
            print "Running %s tests from %s" % (kind, extra)
            self.libdir = extra
            sys.path.insert(0, extra)
        else:
            print "Running %s tests from %s" % (kind, self.cwd)
        # Make sure functional tests find ftesting.zcml
        if functional:
            config_file = 'ftesting.zcml'
            print "Parsing %s" % config_file
            from zope.testing.functional import FunctionalTestSetup
            FunctionalTestSetup(config_file)

def match(rx, s):
    if not rx:
        return True
    if rx[0] == "!":
        return re.search(rx[1:], s) is None
    else:
        return re.search(rx, s) is not None

class TestFileFinder:
    def __init__(self, prefix):
        self.files = []
        self._plen = len(prefix)
        if not prefix.endswith(os.sep):
            self._plen += 1
        global functional
        if functional:
            self.dirname = "ftests"
        else:
            self.dirname = "tests"
        # dirs maps directories to a boolean indicating whether
        # the directory is a package.  Bootstrap dirs with prefix;
        # it isn't actually a package, but it contains packages.
        self.dirs = {prefix: True}

    def is_package(self, dir):
        # Return true if dir contains a testable package.
        bool = self.dirs.get(dir)
        if bool is not None:
            return bool
        files = os.listdir(dir)
        if ".testinfo" in files or "__init__.py" not in files:
            self.dirs[dir] = False
            return False
        parent, dir = os.path.split(dir)
        bool = self.is_package(parent)
        self.dirs[dir] = bool
        return bool

    def visit(self, rx, dir, files):
        if os.path.split(dir)[1] != self.dirname:
            # Allow tests module rather than package.
            if "tests.py" in files:
                path = os.path.join(dir, "tests.py")
                if match(rx, path):
                    self.files.append(path)
                    return 
            return
        if not self.is_package(dir):
            return

        # Put matching files in matches.  If matches is non-empty,
        # then make sure that the package is importable.
        matches = []
        for file in files:
            if file.startswith('test') and os.path.splitext(file)[-1] == '.py':
                path = os.path.join(dir, file)
                if match(rx, path):
                    matches.append(path)

        # ignore tests when the package can't be imported, possibly due to
        # dependency failures.
        pkg = dir[self._plen:].replace(os.sep, '.')
        try:
            __import__(pkg)
        # We specifically do not want to catch ImportError since that's useful
        # information to know when running the tests.
        except RuntimeError, e:
            if VERBOSE:
                print "skipping %s because: %s" % (pkg, e)
            return
        else:
            self.files.extend(matches)

    def module_from_path(self, path):
        """Return the Python package name indicated by the filesystem path."""
        assert path.endswith(".py")
        path = path[self._plen:-3]
        mod = path.replace(os.sep, ".")
        return mod

def find_tests(rx):
    global finder
    finder = TestFileFinder(pathinit.libdir)
    walkdir = test_dir or pathinit.libdir
    os.path.walk(walkdir, finder.visit, rx)
    return finder.files

def package_import(modname):
    mod = __import__(modname)
    for part in modname.split(".")[1:]:
        mod = getattr(mod, part)
    return mod

class PseudoTestCase:
    """Minimal test case objects to create error reports.

    If test.py finds something that looks like it should be a test but
    can't load it or find its test suite, it will report an error
    using a PseudoTestCase.
    """

    def __init__(self, name, descr=None):
        self.name = name
        self.descr = descr

    def shortDescription(self):
        return self.descr

    def __str__(self):
        return "Invalid Test (%s)" % self.name

def get_suite(file, result):
    modname = finder.module_from_path(file)
    try:
        mod = package_import(modname)
        return mod.test_suite()
    except AttributeError:
        result.addError(PseudoTestCase(modname), sys.exc_info())
        return None

def filter_testcases(s, rx):
    new = unittest.TestSuite()
    for test in s._tests:
        # See if the levels match
        dolevel = (level == 0) or level >= getattr(test, "level", 0)
        if not dolevel:
            continue
        if isinstance(test, unittest.TestCase):
            name = test.id() # Full test name: package.module.class.method
            name = name[1 + name.rfind("."):] # extract method name
            if not rx or match(rx, name):
                new.addTest(test)
        else:
            filtered = filter_testcases(test, rx)
            if filtered:
                new.addTest(filtered)
    return new

def gui_runner(files, test_filter):
    utildir = os.path.join(os.getcwd(), "utilities")
    sys.path.append(utildir)
    import unittestgui
    suites = []
    for file in files:
        suites.append(finder.module_from_path(file) + ".test_suite")

    suites = ", ".join(suites)
    minimal = (GUI == "minimal")
    unittestgui.main(suites, minimal)

class TrackRefs:
    """Object to track reference counts across test runs."""

    def __init__(self):
        self.type2count = {}
        self.type2all = {}

    def update(self):
        import types
        obs = sys.getobjects(0)
        type2count = {}
        type2all = {}
        classes = []
        for o in obs:
            all = sys.getrefcount(o)
            t = type(o)
            if t is types.ClassType:
                classes.append((all, o))
            if t in type2count:
                type2count[t] += 1
                type2all[t] += all
            else:
                type2count[t] = 1
                type2all[t] = all

        ct = [(type2count[t] - self.type2count.get(t, 0),
               type2all[t] - self.type2all.get(t, 0),
               t)
              for t in type2count.iterkeys()]
        ct.sort()
        ct.reverse()
        for delta1, delta2, t in ct:
            if delta1 or delta2:
                print "%-55s %8d %8d" % (t, delta1, delta2)

        classes.sort()
        classes.reverse()
        for n, c in classes[:10]:
            print n, c

        self.type2count = type2count
        self.type2all = type2all

def runner(files, test_filter, debug):
    runner = ImmediateTestRunner(verbosity=VERBOSE, debug=debug,
                                 progress=progress)
    suite = unittest.TestSuite()
    for file in files:
        s = get_suite(file, runner.result)
        # See if the levels match
        dolevel = (level == 0) or level >= getattr(s, "level", 0)
        if s is not None and dolevel:
            s = filter_testcases(s, test_filter)
            suite.addTest(s)
    try:
        r = runner.run(suite)
        if timesfn:
            r.print_times(open(timesfn, "w"))
            if VERBOSE:
                print "Wrote timing data to", timesfn
        if timetests:
            r.print_times(sys.stdout, timetests)
    except:
        if debugger:
            pdb.post_mortem(sys.exc_info()[2])
        else:
            raise

def remove_stale_bytecode(arg, dirname, names):
    names = map(os.path.normcase, names)
    for name in names:
        if name.endswith(".pyc") or name.endswith(".pyo"):
            srcname = name[:-1]
            if srcname not in names:
                fullname = os.path.join(dirname, name)
                print "Removing stale bytecode file", fullname
                os.unlink(fullname)

def main(module_filter, test_filter, libdir):
    if not keepStaleBytecode:
        os.path.walk(os.curdir, remove_stale_bytecode, None)

    global pathinit

    configure_logging()

    # Initialize the path and cwd
    pathinit = PathInit(build, libdir)

    files = find_tests(module_filter)
    files.sort()

    if GUI:
        gui_runner(files, test_filter)
    elif LOOP:
        if REFCOUNT:
            rc = sys.gettotalrefcount()
            track = TrackRefs()
        while True:
            runner(files, test_filter, debug)
            gc.collect()
            if gc.garbage:
                print "GARBAGE:", len(gc.garbage), gc.garbage
                return
            if REFCOUNT:
                prev = rc
                rc = sys.gettotalrefcount()
                print "totalrefcount=%-8d change=%-6d" % (rc, rc - prev)
                track.update()
    else:
        runner(files, test_filter, debug)


def configure_logging():
    """Initialize the logging module."""
    import logging.config

    # Get the log.ini file from the current directory instead of possibly
    # buried in the build directory.  XXX This isn't perfect because if
    # log.ini specifies a log file, it'll be relative to the build directory.
    # Hmm...
    logini = os.path.abspath("log.ini")

    if os.path.exists(logini):
        logging.config.fileConfig(logini)
    else:
        logging.basicConfig()

    if os.environ.has_key("LOGGING"):
        level = int(os.environ["LOGGING"])
        logging.getLogger().setLevel(level)


def process_args(argv=None):
    import getopt
    global module_filter
    global test_filter
    global VERBOSE
    global LOOP
    global GUI
    global TRACE
    global REFCOUNT
    global debug
    global debugger
    global build
    global level
    global libdir
    global timesfn
    global timetests
    global progress
    global keepStaleBytecode
    global functional
    global test_dir

    if argv is None:
        argv = sys.argv

    module_filter = None
    test_filter = None
    VERBOSE = 0
    LOOP = False
    GUI = False
    TRACE = False
    REFCOUNT = False
    debug = False # Don't collect test results; simply let tests crash
    debugger = False
    build = False
    gcthresh = None
    gcdebug = 0
    gcflags = []
    level = 1
    libdir = None
    progress = False
    timesfn = None
    timetests = 0
    keepStaleBytecode = 0
    functional = False
    test_dir = None

    try:
        opts, args = getopt.getopt(argv[1:], "a:bcdDfg:G:hLmprtTuv",
                                   ["all", "help", "libdir=", "times=",
                                    "keepbytecode", "dir="])
    except getopt.error, msg:
        print msg
        print "Try `python %s -h' for more information." % argv[0]
        sys.exit(2)

    for k, v in opts:
        if k == "-a":
            level = int(v)
        elif k == "--all":
            level = 0
        elif k == "-b":
            build = True
        elif k == "-c":
            # make sure you have a recent version of pychecker
            if not os.environ.get("PYCHECKER"):
                os.environ["PYCHECKER"] = "-q"
            import pychecker.checker
        elif k == "-d":
            debug = True
        elif k == "-D":
            debug = True
            debugger = True
        elif k == "-f":
            functional = True
        elif k in ("-h", "--help"):
            print __doc__
            sys.exit(0)
        elif k == "-g":
            gcthresh = int(v)
        elif k == "-G":
            if not v.startswith("DEBUG_"):
                print "-G argument must be DEBUG_ flag, not", repr(v)
                sys.exit(1)
            gcflags.append(v)
        elif k == '--keepbytecode':
            keepStaleBytecode = 1
        elif k == '--libdir':
            libdir = v
        elif k == "-L":
            LOOP = 1
        elif k == "-m":
            GUI = "minimal"
        elif k == "-p":
            progress = True
        elif k == "-r":
            if hasattr(sys, "gettotalrefcount"):
                REFCOUNT = True
            else:
                print "-r ignored, because it needs a debug build of Python"
        elif k == "-T":
            TRACE = True
        elif k == "-t":
            if not timetests:
                timetests = 50
        elif k == "-u":
            GUI = 1
        elif k == "-v":
            VERBOSE += 1
        elif k == "--times":
            try:
                timetests = int(v)
            except ValueError:
                # must be a filename to write
                timesfn = v
        elif k == '--dir':
            test_dir = v

    if gcthresh is not None:
        if gcthresh == 0:
            gc.disable()
            print "gc disabled"
        else:
            gc.set_threshold(gcthresh)
            print "gc threshold:", gc.get_threshold()

    if gcflags:
        val = 0
        for flag in gcflags:
            v = getattr(gc, flag, None)
            if v is None:
                print "Unknown gc flag", repr(flag)
                print gc.set_debug.__doc__
                sys.exit(1)
            val |= v
        gcdebug |= v

    if gcdebug:
        gc.set_debug(gcdebug)

    if build:
        # Python 2.3 is more sane in its non -q output
        if sys.hexversion >= 0x02030000:
            qflag = ""
        else:
            qflag = "-q"
        cmd = sys.executable + " setup.py " + qflag + " build_ext -i"
        if VERBOSE:
            print cmd
        sts = os.system(cmd)
        if sts:
            print "Build failed", hex(sts)
            sys.exit(1)

    if VERBOSE:
        kind = functional and "functional" or "unit"
        if level == 0:
            print "Running %s tests at all levels" % kind
        else:
            print "Running %s tests at level %d" % (kind, level)

    if args:
        if len(args) > 1:
            test_filter = args[1]
        module_filter = args[0]
    try:
        if TRACE:
            # if the trace module is used, then we don't exit with
            # status if on a false return value from main.
            coverdir = os.path.join(os.getcwd(), "coverage")
            import trace
            tracer = trace.Trace(ignoredirs=[sys.prefix, sys.exec_prefix],
                                 trace=0, count=1)

            tracer.runctx("main(module_filter, test_filter, libdir)",
                          globals=globals(), locals=vars())
            r = tracer.results()
            r.write_results(show_missing=True, summary=True, coverdir=coverdir)
        else:
            bad = main(module_filter, test_filter, libdir)
            if bad:
                sys.exit(1)
    except ImportError, err:
        print err
        print sys.path
        raise


if __name__ == "__main__":
    process_args()
