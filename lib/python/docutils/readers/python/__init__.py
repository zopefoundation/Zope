# Author: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.3 $
# Date: $Date: 2003/11/30 15:06:08 $
# Copyright: This module has been placed in the public domain.

"""
This package contains the Python Source Reader modules.
"""

__docformat__ = 'reStructuredText'


import sys
import docutils.readers


class Reader(docutils.readers.Reader):

    config_section = 'python reader'
    config_section_dependencies = ('readers',)
