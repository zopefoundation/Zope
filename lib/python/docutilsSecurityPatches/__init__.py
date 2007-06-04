##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
""" security patches for docutils """

try:
    import docutils
except ImportError:
    raise ImportError, 'Please install docutils 0.4.0+ from http://docutils.sourceforge.net/#download.'

version = docutils.__version__.split('.')
if not (version >= ['0', '4', '0'] or  version >= ['0', '4']):
    raise ImportError, """Old version of docutils found:
Got: %(version)s, required: 0.4.0+
Please remove docutils from %(path)s and replace it with a new version. You
can download docutils at http://docutils.sourceforge.net/#download.
""" % {'version' : docutils.__version__, 'path' : docutils.__path__[0] }


# disable inclusion of files for security reasons
# this way we don't need a custom version of docutils anymore
import docutils.parsers.rst.directives.misc

# additional import needed here since raw's func_code was swapped below...
from docutils import nodes

def include(*args, **kw):
    """ disabled for security reasons """
    raise NotImplementedError, 'File inclusion not allowed!'
docutils.parsers.rst.directives.misc.include.func_code = include.func_code

def raw_orig(*args, **kw):
    """ place holder for original copy of function """
    pass
raw_orig.func_code = docutils.parsers.rst.directives.misc.raw.func_code
docutils.parsers.rst.directives.misc.raw_orig = raw_orig

def raw(name, arguments, options, *args, **kw):
    """ disabled specific options for security reasons """
    if options.has_key('file') or options.has_key('url'):
        raise NotImplementedError, 'File inclusion not allowed!'
    return raw_orig(name, arguments, options, *args, **kw)
docutils.parsers.rst.directives.misc.raw.func_code = raw.func_code

