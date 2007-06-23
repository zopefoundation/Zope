The Testing package is a set of shared routines for the Zope unit
testing framework. From Zope 2.8 these are more easily accessed
by using the ZopeTestCase package. See ZopeTestCase/doc for more
information.


To use Testing without ZopeTestCase:

1. Make a 'tests' subdirectory.

2. Copy 'framework.py' into 'tests' from any other package's 'tests'.

Once a test suite has been set up, you can add test modules:

1. Create a file with a name matching 'test*.py'.

2. Define one or more subclasses of 'unittest.TestCase'.  The unittest
   module is imported by the framework.

3. Define methods for the test classes.  Each method's name must start
   with 'test'.  It should test one small case, using a Python
   'assert' statement.  Here's a minimal example:

   class testClass1(unittest.TestCase):
       def testAddition(self):
           assert 1 + 1 == 2, 'Addition failed!'

4. You can add 'setUp' and 'tearDown' methods that are automatically
   called at the start and end of the test suite.

5. Follow the instructions in 'framework.py' about adding lines to the
   top and bottom of the file.

Now you can run the test as "python path/to/tests/testName.py", or
simply go to the 'tests' directory and type "python testName.py".
