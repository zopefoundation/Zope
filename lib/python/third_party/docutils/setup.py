#!/usr/bin/env python
# $Id: setup.py,v 1.1.4.1 2004/10/29 19:08:15 andreasjung Exp $
# Copyright: This file has been placed in the public domain.

import sys
import os
from distutils.core import setup
from distutils.command.build_py import build_py


def do_setup():
    kwargs = package_data.copy()
    extras = get_extras()
    if extras:
        kwargs['py_modules'] = extras
    if sys.hexversion >= 0x02030000:    # Python 2.3
        kwargs['classifiers'] = classifiers
    else:
        kwargs['cmdclass'] = {'build_py': dual_build_py}
    dist = setup(**kwargs)
    return dist

package_data = {
    'name': 'docutils',
    'description': 'Docutils -- Python Documentation Utilities',
    'long_description': """\
Docutils is a modular system for processing documentation
into useful formats, such as HTML, XML, and LaTeX.  For
input Docutils supports reStructuredText, an easy-to-read,
what-you-see-is-what-you-get plaintext markup syntax.""", # wrap at col 60
    'url': 'http://docutils.sourceforge.net/',
    'version': '0.3.5',
    'author': 'David Goodger',
    'author_email': 'goodger@users.sourceforge.net',
    'license': 'public domain, Python, BSD, GPL (see COPYING.txt)',
    'platforms': 'OS-independent',
    'package_dir': {'docutils': 'docutils', '': 'extras'},
    'packages': ['docutils', 'docutils.languages',
                 'docutils.parsers', 'docutils.parsers.rst',
                 'docutils.parsers.rst.directives',
                 'docutils.parsers.rst.languages',
                 'docutils.readers', 'docutils.readers.python',
                 'docutils.transforms',
                 'docutils.writers',],
    'scripts' : ['tools/rst2html.py','tools/rst2latex.py'],}
"""Distutils setup parameters."""

classifiers = [
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: End Users/Desktop',
    'Intended Audience :: Other Audience',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'License :: Public Domain',
    'License :: OSI Approved :: Python Software Foundation License',
    'License :: OSI Approved :: BSD License',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Documentation',
    'Topic :: Software Development :: Documentation',
    'Topic :: Text Processing',
    'Natural Language :: English',      # main/default language, keep first
    'Natural Language :: Afrikaans',
    'Natural Language :: Esperanto',
    'Natural Language :: French',
    'Natural Language :: German',
    'Natural Language :: Italian',
    'Natural Language :: Russian',
    'Natural Language :: Slovak',
    'Natural Language :: Spanish',
    'Natural Language :: Swedish',]
"""Trove classifiers for the Distutils "register" command;
Python 2.3 and up."""

extra_modules = [('optparse', '1.4.1', None),
                 ('textwrap', None, None),
                 ('roman', '1.4', ['toRoman', 'fromRoman',
                                   'InvalidRomanNumeralError'])]
"""Third-party modules to install if they're not already present.
List of (module name, minimum __version__ string, [attribute names])."""

def get_extras():
    extras = []
    for module_name, version, attributes in extra_modules:
        try:
            module = __import__(module_name)
            if version and module.__version__ < version:
                raise ValueError
            for attribute in attributes or []:
                getattr(module, attribute)
            print ('"%s" module already present; ignoring extras/%s.py.'
                   % (module_name, module_name))
        except (ImportError, AttributeError, ValueError):
            extras.append(module_name)
    return extras


class dual_build_py(build_py):

    """
    This class allows the distribution of both packages *and* modules with one
    call to `distutils.core.setup()` (necessary for pre-2.3 Python).  Thanks
    to Thomas Heller.
    """

    def run(self):
        if not self.py_modules and not self.packages:
            return
        if self.py_modules:
            self.build_modules()
        if self.packages:
            self.build_packages()
        self.byte_compile(self.get_outputs(include_bytecode=0))


if __name__ == '__main__' :
    do_setup()
