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

""" Request log profiler script """

__version__='$Revision: 1.1 $'[11:-2]

import string, sys, time, getopt

class Request:
    def __init__(self):
        self.start = 0
        self.end = 0
        self.elapsed = "I"
        self.url = ''
        
    def put(self, code, t, desc):
        if code not in ('A', 'B', 'I', 'E'):
            raise "unknown request code %s" % code
        if code == 'B':
            self.url = desc
            self.start = t
        if code == 'E':
            self.end = t
            self.elapsed = int(self.end - self.start)
    
class Cumulative:
    def __init__(self, url):
        self.url = url
        self.requests = []
        self.hangs = 0
        self.allelapsed = None
        
    def put(self, request):
        if not request.end:
            self.hangs = self.hangs + 1
        self.requests.append(request)
            
    def all(self):
        if self.allelapsed == None:
            self.allelapsed = []
            for request in self.requests:
                self.allelapsed.append(request.elapsed)
            self.allelapsed.sort()
        return self.allelapsed

    def __str__(self):
        if verbose:
            url = self.url
        else:
            url = self.url[:22]
        s = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
            self.hangs,
            self.hits(),
            self.total(),
            self.max(),
            self.min(),
            self.median(),
            self.mean(),
            url
            )
        return s

    def hits(self):
        return len(self.requests)
        
    def max(self):
        return max(self.all())
        
    def min(self):
        return min(self.all())
        
    def mean(self):
        l = len(self.requests)
        if l == 0:
            return "I"
        else:
            t = self.total()
            if t == "I": return "I"
            return t/l
        
    def median(self):
        all = self.all()
        l = len(all)
        if l == 0:
            return "I"
        else:
            if l == 1:
                return all[0]
            elif l % 2 != 0:
                i = l/2 + 1
                return all[i]
            else:
                i = l/2 - 1
                i2 = i + 1
                v1 = all[i]
                v2 = all[i2]
                if v1 == "I" or v2 == "I": return "I"
                else: return (all[i] + all[i2]) / 2
    
    def total(self):
        t = 0
        all = self.all()
        if len(all) == 1:
            return all[0]
        for elapsed in self.all():
            if elapsed != "I":
                t = t + elapsed
        return t

def analyze(f, top, sortf):
    requests={}
    while 1:
        line = f.readline()
        line = string.strip(line)
        if not line:
            break
        tup = string.split(line, None, 3)
        if len(tup) == 3:
            code, id, timestr = tup
            desc = ''
        elif len(tup) == 4:
            code, id, timestr, desc = tup
        else:
            continue
        gmtimetup = time.strptime(timestr, '%Y-%m-%dT%H:%M:%S')
        fromepoch = time.mktime(gmtimetup)
        request = requests.get(id)
        if request is None:
            request = Request()
            requests[id] = request
        request.put(code, fromepoch, desc)

    requests = requests.values()
    cumulative = {}
    for request in requests:
        url = request.url
        stats = cumulative.get(url)
        if stats is None:
            stats = Cumulative(url)
            cumulative[url] = stats
        stats.put(request)
    requests = cumulative.values()
    requests.sort(sortf)
    write(requests, top, "Hangs\tHits\tTotal\tMax\tMin\tMedian\tMean\tURL")
        
def write(requests, top=0, header=''):
        i = 0
        print header 
        for stat in requests:
            i = i + 1
            print stat
            if i == top:
                break

class Sort:
    def __init__(self, fname, ascending=0):
        self.fname = fname
        self.ascending = ascending

    def __call__(self, i1, i2):
        f1 = getattr(i1, self.fname)
        f2 = getattr(i2, self.fname)
        if callable(f1): f1 = f1()
        if callable(f2): f2 = f2()
        if f1 < f2:
            if self.ascending: return -1
            else: return 1
        elif f1 == f2:
            return 0
        else:
            if self.ascending: return 1
            else: return -1
            
def detailedusage():
    details = usage(0)
    details = details + """
Each line in the profile indicates information about a Zope method (URL)
collected via the detailed request log (the -M log).

'filename' is the path to the '-M' log that contains detailed request data.

If a 'sort' value is specified, sort the profile info by the spec. The sort
spec may be any of 'hits', 'hangs', 'max', 'min', 'mean', 'median', or 'total'.
The default is 'total'.  The sort order is decending unless indicated.

  'hits'       -- the number of hits against the method
  'hangs'      -- the number of unfinished requests to the method
  'max'        -- the maximum time in secs taken by a request to this method
  'min'        -- the minimum time in secs taken by a request to this method
  'mean'       -- the mean time in secs taken by a request to this method
  'median'     -- the median time in secs taken by a request to this method
  'total'      -- the total time in secs across all requests to this method
  'url'        -- the URL/method name (ascending)

If the 'top' argument is specified, only report on the top 'n' requests in
the log (as per the sort).  The default is 10.

If the 'verbose' argument is specified, do not trim url to fit into 80 cols."""
    return details

def usage(basic=1):
    usage = (
        """
Usage: %s filename [--sort=spec] [--top=n] [--verbose] [--help]
        
Provides a profile of the detailed (-M) Zope request log.
""" % sys.argv[0]
        )
    if basic == 1:
        usage = usage + """
If the --help argument is given, detailed usage docs are provided."""
    return usage
    
if __name__ == '__main__':
    if len(sys.argv) == 1:
        print usage()
        sys.exit(0)
    if sys.argv[1] == '--help': print detailedusage(); sys.exit(0)
    trim = 0
    top = 10
    verbose = 0
    sortby = 'total'
    try:
        opts, extra = getopt.getopt(
            sys.argv[2:], '', ['sort=', 'top=', 'help', 'verbose']
            )
    except:
        print usage()
        sys.exit(0)
    for opt, val in opts:
        if opt=='--sort': sortby = val
        if opt=='--top': top=int(val)
        if opt=='--help': print detailedusage(); sys.exit(0)
        if opt=='--verbose':
            global verbose
            verbose = 1
        
    if sortby in ['url', 'hits', 'hangs', 'max', 'min', 'median', 'mean',
                  'total']:
        if sortby == 'url':
            # ascending
            sortf = Sort(sortby, ascending=1)
        else:
            sortf = Sort(sortby)
        try:
            analyze(open(sys.argv[1]), top, sortf)
        except:
            import traceback
            traceback.print_exc()
            print usage(); sys.exit(0)
    else:
        print usage()
        sys.exit(0)

