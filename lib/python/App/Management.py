
"""Standard management interface support

$Id: Management.py,v 1.2 1997/08/08 17:25:12 jim Exp $"""

__version__='$Revision: 1.2 $'[11:-2]

import sys,Globals
from Dialogs import MessageDialog
from Globals import ManageHTMLFile

class Management:
    """A mix-in class for basic management interface support.

    Management provides the basic frames-based management interface for an 
    object. For any Management derived instance, the url <object>/manage 
    will return the management interface for that object. The manage 
    attribute is a document template containing a frameset referencing 
    two named frames: "manage_menu" on the left, "manage_main" on the
    right. The "manage_menu" frame will load the manage_menu attribute
    of your instance, The "manage_main" frame will load the instance's
    manage_main attribute.

    manage_menu -- the management menu frame. This is provided by the
                   Management class. It renders menu options based on your
		   instance's manage_options attribute, as described
		   below.

    manage_main -- the "management homepage" frame. This is the default
                   document loaded into the right-hand frame whenever a
		   browser goes to <object>/manage. This page will often
		   be a "status" page, relaying relevant information about
		   the instance being viewed, as well as a link to the
		   "public" interface of the object (index_html).

		   The Management class provides a default document template 
		   that is used for manage_main if the instance does not 
		   override this attribute.

    manage_options -- This attribute is a list of dictionaries containing 
                   information about each menu item to be displayed in
		   the "manage_menu" frame. Subclasses should override the 
		   default manage_options attribute of Management (which is 
		   just an empty list, producing an empty menu).

		   For each dictionary in the list, a menu item will be shown
		   with an icon of dict['icon'], 
		   a label of dict['label'], 
		   linking to <PARENT_URL>/dict['action'], 
		   targeted at the frame dict['target'].

		   If your Management derived class defines a manage_options 
		   attribute:
		   <PRE>

		   manage_options=[{'icon':'foo.gif',
                                    'label':'Go to spam',
                                    'action':'spam_html',
                                    'target':'manage_main'}]

		   </PRE>
		   ...you will get one menu item labelled 'Go to spam', 
		   (with an icon of foo.gif) that is a hyperlink to 
		   <PARENT_URL>/spam_html, and when clicked, the document 
		   will appear in the 'manage_main' frame of the web browser. 
		   If you wanted a new window to appear containing the 
		   document, you would use '_new' as the value of 'target' 
		   in the dictionary for that item.

		   Following these general rules will keep you from 
		   inadvertantly ending up with nested framesets:

		   o If your menu option should take the user to another 
		     attribute of the current object, the target should 
		     be 'manage_main'.

		   o If your menu option should take the user to the public 
		     interface of the current object, the target should be 
		     '_top'.

		   o If your menu option should take the user to the 
		     management or public interface of another object, the 
		     target should be '_top'.

		   o If your menu option should cause a new window to be 
		     opened with the requested document, the target should 
		     be '_new' (This is often useful for things like online 
		     help).

		   A menu item will be generated for each dictionary in the 
		   manage_options list. Sometimes it is useful to provide a 
		   separator between various menu items; to insert a 
		   "separator" line as a menu entry, put an empty dictionary
		   in your manage_options list where you want the separator
		   to appear.
    """

    manage_options      =[]
    manage              =ManageHTMLFile('App/manage')
    manage_menu         =ManageHTMLFile('App/menu')
