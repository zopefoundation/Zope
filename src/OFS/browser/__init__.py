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

from Acquisition import aq_base
from Acquisition import aq_parent
from Products.Five import BrowserView


raiser = 'raise_standardErrorMessage'


class StandardErrorMessageView(BrowserView):
    """ View rendered on SiteError.

    Requires a callable object named ``standard_error_message`` on the
    published object's acquisition path. The callable can be a DTML Method,
    DTML Document, Python Script or Page Template.
    """

    def __call__(self):
        pub = getattr(self.request, 'PUBLISHED', self.request['PARENTS'][0])
        parent = aq_parent(pub)

        if pub is not None and parent is None:
            # The published object is not an instance or not wrapped
            pub = self.request['PARENTS'][0]
            parent = aq_parent(pub)

        if getattr(aq_base(pub), raiser, None) is not None:
            return getattr(pub, raiser)(REQUEST=self.request)[1]

        return parent.standard_error_message(
            client=parent,
            error_type=self.context.__class__.__name__,
            error_value=str(self.context))
