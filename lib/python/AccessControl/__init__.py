__doc__="""$Id: __init__.py,v 1.1 1997/08/26 18:54:42 brian Exp $"""
__version__='$Revision: 1.1 $'[11:-2]

import User

__.meta_types=({'name':'User Folder',
                'action':'manage_addUserFolder'
	       },
	       )

__.methods={'manage_addUserFolder':
             User.manage_addUserFolder,
	    }
