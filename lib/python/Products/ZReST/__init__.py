# 
# $Id$
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

