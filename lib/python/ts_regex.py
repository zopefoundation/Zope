##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""
Replacement of the old ts_regex module using the standard re module
"""

import re,reconvert
import sys

import ts_regex_old as OLD
import ts_regex_new as NEW


def _rcCV(s):

    cs = reconvert.convert(s)
    if cs != s:
        print 'Warning: "%s" must be converted to "%s"' % (s,cs)

    return cs


def sub(pat,repl,str):
    x = OLD.sub(pat,repl,str)
    y = NEW.sub(pat,repl,str)
    if x!=y: print 'Warning: sub():',pat,repl,str
    return x

def gsub(pat,repl,str):
    x = OLD.gsub(pat,repl,str)
    y = NEW.gsub(pat,repl,str)
    if x!=y: print 'Warning: subg():',pat,repl,str
    return x


def split(str,pat,maxsplit=0):
    x = OLD.split(str,pat,maxsplit)
    y = NEW.split(str,pat,maxsplit)
    if x!=y: print 'Warning: split():',str,pat,maxsplit
    return x


def splitx(str,pat,maxsplit=0):
    x = OLD.splitx(str,pat,maxsplit)
    y = NEW.splitx(str,pat,maxsplit)
    if x!=y: print 'Warning: splitx():',str,pat,maxsplit
    return x
    


class compile:

    def __init__(self, *args):
        print>>sys.stderr, args
        self._old = apply(OLD.compile,args)
        self._new = apply(NEW.compile,args)


    def match(self, string, pos=0):
        x = self._old.match(string,pos)
        y = self._new.match(string,pos)
        if x!=y: print 'Warning: match():',string,pos
        return x


    def search(self, string, pos=0):
        x = self._old.search(string,pos)
        y = self._new.search(string,pos)
        if x!=y: print 'Warning: search():',string,pos
        return x
 
    def search_group(self, str, group, pos=0):
        """Search a string for a pattern.

        If the pattern was not found, then None is returned,
        otherwise, the location where the pattern was found,
        as well as any specified group are returned.
        """
        x = self._old.search_group(str,group,pos)
        y = self._new.search_group(str,group,pos)
        if x!=y: print 'Warning: seach_group(%s,%s,%s) %s vs %s' % (str,group,pos,x,y)
        return x


    def match_group(self, str, group, pos=0):
        """Match a pattern against a string

        If the string does not match the pattern, then None is
        returned, otherwise, the length of the match, as well
        as any specified group are returned.
        """
        x = self._old.match_group(str,group,pos)
        y = self._new.match_group(str,group,pos)
        if x!=y: 
            print 'Warning: match_group(%s,%s,%s) %s vs %s' % (str,group,pos,x,y)
            print self._old.givenpat
            print self._new.givenpat
        return x

      

if __name__=='__main__':

    import sys

    s1 = 'The quick brown fox jumps of The lazy dog'
    s2 = '892 The quick brown 123 fox jumps over  3454 21 The lazy dog'

    r1 = ' [a-zA-Z][a-zA-Z] '
    r2 = '[0-9][0-9]'
    print 'new:',split(s1,' ')
    print 'new:',splitx(s2,' ')
    print 'new:',split(s2,' ',2)
    print 'new:',splitx(s2,' ',2)
    print 'new:',sub('The','###',s1)
    print 'new:',gsub('The','###',s1)

    p1 = compile(r1)
    p2 = compile(r2)

    for s in [s1,s2]:


      print 'search' 

      print 'new:',p1.search(s)
      print 'new:',p2.search(s)

      print 'match' 
      print 'new:',p1.match(s)
      print 'new:',p2.match(s)
 

      print 'match_group'
      print 'new:',p1.match_group(s,(0,))
      print 'new:',p2.match_group(s,(0,))


      print 'search_group'
      print 'new:',p1.match_group(s,(0,1))
      print 'new:',p2.match_group(s,(0,1))
