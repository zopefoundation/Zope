#!/usr/bin/env python
# $Id: install.py,v 1.1.4.1 2004/10/29 19:08:15 andreasjung Exp $
# Copyright: This file has been placed in the public domain.

"""
This is a quick & dirty installation shortcut. It is equivalent to the
command::

    python setup.py install

However, the shortcut lacks error checking and command-line option
processing.  If you need any kind of customization or help, please use
one of::

    python setup.py install --help
    python setup.py --help
"""

from distutils import core
from setup import do_setup

if __name__ == '__main__' :
    print __doc__
    core._setup_stop_after = 'config'
    dist = do_setup()
    dist.commands = ['install']
    dist.run_commands()
