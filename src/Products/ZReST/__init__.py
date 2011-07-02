# product initialisation
import ZReST
def initialize(context):
    context.registerClass(
        ZReST.ZReST,
        meta_type = 'ReStructuredText Document',
        constructors = (ZReST.manage_addZReSTForm, ZReST.manage_addZReST)
    )
