# 
# $Id: __init__.py,v 1.4 2004/01/18 10:21:19 andreasjung Exp $
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


#
# $Log: __init__.py,v $
# Revision 1.4  2004/01/18 10:21:19  andreasjung
# added icon provided by Jeff Kowalyzyk
#
# Revision 1.3  2003/08/16 00:54:35  chrism
# Initialize the class, not the module.
#
# Revision 1.2  2003/02/01 09:28:30  andreasjung
# merge from ajung-restructuredtext-integration-branch
#
# Revision 1.1.2.2  2002/11/06 16:09:36  andreasjung
# updated to ZReST 1.1
#
# Revision 1.2  2002/08/15 04:36:56  richard
# FTP interface and Reporter message snaffling
#
# Revision 1.1  2002/08/14 05:15:37  richard
# Zope ReStructuredText Product
#
#
#
# vim: set filetype=python ts=4 sw=4 et si
