# 
# $Id: __init__.py,v 1.5 2004/01/18 10:25:57 andreasjung Exp $
#
__version__='1.0'

# product initialisation
import ZReST
def initialize(context):
    context.registerClass(
        ZReST.ZReST,
        meta_type = 'ReStructuredText Document',
        icon='www/zrest.gif',
        constructors = (
            ZReST.manage_addZReSTForm, ZReST.manage_addZReST
        )
    )

