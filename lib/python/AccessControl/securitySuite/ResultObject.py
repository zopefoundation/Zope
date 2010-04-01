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


class ResultObject:
    """ result object used for keeping results from the
        ZPublisher.Zope() calls

        $Id$
    """

    def __str__(self,expected=-1,with_output=1):
        s  = '\n'
        s+= '-'*78
        s+= "\nRequest: %s" % self.request
        s+= "\nUser: %s" % self.user
        s+= "\nExpected: %s" % expected + "  got: %s %s" % (self.code,self.return_text)
        if with_output:
            s+= "\nOutput:"
            s+= self.output
        s+= "\n"

        return s

    __repr__ = __str__

    def __call__(self,expected=-1):
        return self.__str__(expected)
