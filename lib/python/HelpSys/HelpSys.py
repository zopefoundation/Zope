"""Help system implementation"""

__version__='$Revision: 1.4 $'[11:-2]


import sys, os, string, Globals, Acquisition
from HelpUtil import HelpBase
from ObjectRef import ObjectRef
from ImageFile import ImageFile
from Globals import HTMLFile





class HelpSys(HelpBase):
    """ """
    __names__=None
    __roles__=None

    hs_index=HTMLFile('helpsys', globals())
    hs_menu =HTMLFile('helpsys_menu', globals())
    hs_main =HTMLFile('helpsys_main', globals())

    hs_cicon='HelpSys/hs_cbook'
    hs_eicon='HelpSys/hs_obook'
    
    # Images used by the help system
    hs_uarrow=ImageFile('images/hs_uarrow.gif', globals())
    hs_darrow=ImageFile('images/hs_darrow.gif', globals())
    hs_rarrow=ImageFile('images/hs_rarrow.gif', globals())
    hs_larrow=ImageFile('images/hs_larrow.gif', globals())
    hs_dnode=ImageFile('images/hs_dnode.gif', globals())
    hs_obook=ImageFile('images/hs_obook.gif', globals())
    hs_cbook=ImageFile('images/hs_cbook.gif', globals())
    
    hs_id='HelpSys'
    hs_title='Z Help Online'

    ObjectRef=ObjectRef()

    hs_objectvalues__roles__=None
    def hs_objectvalues(self):
        return [self.ObjectRef]

    def __len__(self):
        return 1




