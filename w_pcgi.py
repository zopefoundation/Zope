"""Try to do all of the installation steps.

This must be run from the top-level directory of the installation.
(Yes, this is cheezy.  We'll fix this when we have a chance.

"""

import os
home=os.getcwd()
import build_pcgi
import make_resource
os.chdir(home) # Just making sure
import wo_pcgi
