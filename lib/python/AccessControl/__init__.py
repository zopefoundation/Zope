__doc__="""$Id: __init__.py,v 1.2 1997/08/26 22:01:07 brian Exp $"""
__version__='$Revision: 1.2 $'[11:-2]

import User

__.meta_types=({'name':'User Folder',
                'action':'manage_addUserFolder'
	       },
	       )

__.methods={'manage_addUserFolder':
             User.manage_addUserFolder,
	    }

__.role_names=()
