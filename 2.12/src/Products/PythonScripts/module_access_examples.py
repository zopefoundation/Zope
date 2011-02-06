'''Examples for enabling Script import

This file contains example code that can be used to make various
standard Python modules available to Scripts.

In order to use the example code, create a directory called
"MyScriptModules", or something equally descriptive, in your
Zope's "Products" directory.  Copy this file to a file called
"__init__.py" in the new directory.  Edit the new file,
uncommenting the block of code for each module that you want to
make available for import by Scripts.

You can, of course, add your own code to your "__init__.py" for
modules that are not listed below.  The list is not comprehensive,
but is provided as a decent cross-section of modules.

NB:  Placing security assestions within the package/module you are trying 
     to import will not work unless that package/module is located in
     your Products directory.
 
     This is because that package/module would have to be imported for its
     included security assertions to take effect, but to do
     that would require importing a module without any security
     declarations, which defeats the point of the restricted
     python environment.

     Products work differently as they are imported at Zope startup.
     By placing a package/module in your Products directory, you are
     asserting, among other things, that it is safe for Zope to check 
     that package/module for security assertions. As a result, please 
     be careful when place packages or modules that are not Zope Products 
     in the Products directory.
'''

from AccessControl import allow_module, allow_class, allow_type
from AccessControl import ModuleSecurityInfo


# These modules are pretty safe


# allow_module('base64')

# allow_module('binascii')

# allow_module('bisect')

# allow_module('colorsys')

# allow_module('crypt')


# Only parts of these modules should be exposed


# ModuleSecurityInfo('fnmatch').declarePublic('fnmatch', 'fnmatchcase')

# ModuleSecurityInfo('re').declarePublic('compile', 'findall',
#   'match', 'search', 'split', 'sub', 'subn', 'error',
#   'I', 'L', 'M', 'S', 'X')
# import re
# allow_type(type(re.compile('')))
# allow_type(type(re.match('x','x')))

# ModuleSecurityInfo('StringIO').declarePublic('StringIO')


# These modules allow access to other servers


# ModuleSecurityInfo('ftplib').declarePublic('FTP', 'all_errors',
#   'error_reply', 'error_temp', 'error_perm', 'error_proto')
# from ftplib import FTP
# allow_class(FTP)

# ModuleSecurityInfo('httplib').declarePublic('HTTP')
# from httplib import HTTP
# allow_class(HTTP)

# ModuleSecurityInfo('nntplib').declarePublic('NNTP',
#   'error_reply', 'error_temp', 'error_perm', 'error_proto')
# from httplib import NNTP
# allow_class(NNTP)
