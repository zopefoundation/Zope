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
'''

from AccessControl import allow_module, allow_class, allow_type
from AccessControl import ModuleSecurityInfo, ClassSecurityInfo
from Globals import InitializeClass


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
