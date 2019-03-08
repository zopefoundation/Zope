##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from Products.Five import BrowserView


class StandardErrorMessageView(BrowserView):
    """ View rendered on SiteError.
    
    Requires a DTML Method named ``standard_error_message``
    """

    def __call__(self):
        root = self.request['PARENTS'][-1]
        return root.standard_error_message(
            error_type=self.context.__class__.__name__,
            error_value=str(self.context))
