##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__='''MailHost Product Initialization
$Id$'''
__version__='$Revision: 1.22 $'[11:-2]

import MailHost
import SendMailTag

def initialize(context):
    context.registerClass(
        MailHost.MailHost,
        permission='Add MailHost objects',
        constructors=(MailHost.manage_addMailHostForm,
                      MailHost.manage_addMailHost),
        icon='www/MailHost_icon.gif',
    )

    context.registerHelp()
    context.registerHelpTitle('Zope Help')
