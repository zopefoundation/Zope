#!/usr/bin/env python

##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

""" Request log profiler script """

__version__='$Revision: 1.15 $'[11:-2]

import string, sys, time, getopt, tempfile, math, cPickle

class ProfileException(Exception): pass

class Request:
    def __init__(self):
        self.url = None
        self.start = None
        self.method = None
        self.t_recdinput = None
        self.isize = None
        self.t_recdoutput = None
        self.osize = None
        self.httpcode = None
        self.t_end = None
        self.elapsed = "I"
        self.active = 0
        
    def put(self, code, t, desc):
        if code not in ('A', 'B', 'I', 'E'):
            raise "unknown request code %s" % code
        if code == 'B':
            self.start = t
            self.method, self.url = string.split(string.strip(desc))
        elif code == "I":
            self.t_recdinput = t
            self.isize = string.strip(desc)
        elif code == "A":
            self.t_recdoutput = t
            self.httpcode, self.osize = string.split(string.strip(desc))
        elif code == 'E':
            self.t_end = t
            self.elapsed = int(self.t_end - self.start)
            
    def isfinished(self):
        return not self.elapsed == "I"

    def prettystart(self):
        if self.start is not None:
            t = time.localtime(self.start)
            return time.strftime('%Y-%m-%dT%H:%M:%S', t)
        else:
            return "NA"

    def shortprettystart(self):
        if self.start is not None:
            t = time.localtime(self.start)
            return time.strftime('%H:%M:%S', t)
        else:
            return "NA"
        
    def win(self):
        if self.t_recdinput is not None and self.start is not None:
            return self.t_recdinput - self.start
        else:
            return "NA"
        
    def wout(self):
        if self.t_recdoutput is not None and self.t_recdinput is not None:
            return self.t_recdoutput - self.t_recdinput
        else:
            return "NA"

    def wend(self):
        if self.t_end is not None and self.t_recdoutput is not None:
            return self.t_end - self.t_recdoutput
        else:
            return "NA"

    def endstage(self):
        if self.t_end is not None:
            stage = "E"
        elif self.t_recdoutput is not None:
            stage = "A"
        elif self.t_recdinput is not None:
            stage = "I"
        else:
            stage = "B"
        return stage

    def total(self):
        stage = self.endstage()
        if stage == "B": return 0
        if stage == "I": return self.t_recdinput - self.start
        if stage == "A": return self.t_recdoutput - self.start
        if stage == "E": return self.elapsed

    def prettyisize(self):
        if self.isize is not None:
            return self.isize
        else:
            return "NA"

    def prettyosize(self):
        if self.osize is not None:
            return self.osize
        else:
            return "NA"

    def prettyhttpcode(self):
        if self.httpcode is not None:
            return self.httpcode
        else:
            return "NA"

    def __str__(self):
        body = (
            self.prettystart(), self.win(), self.wout(), self.wend(),
            self.total(), self.endstage(), self.prettyosize(),
            self.prettyhttpcode(), self.active, self.url
            )
        return self.fmt % body 

    fmt = "%19s %4s %4s %4s %3s %1s %7s %4s %4s %s"

    def getheader(self):
        body = ('Start', 'WIn', 'WOut', 'WEnd', 'Tot', 'S', 'OSize',
                'Code', 'Act', 'URL')
        return self.fmt % body

class StartupRequest(Request):
    def endstage(self):
        return "U"
        
    def total(self):
        return 0

class Cumulative:
    def __init__(self, url):
        self.url = url
        self.times = []
        self.hangs = 0
        self.allelapsed = None
        
    def put(self, request):
        elapsed = request.elapsed
        if elapsed == "I": self.hangs = self.hangs + 1
        self.times.append(elapsed)
        
    def all(self):
        if self.allelapsed == None:
            self.allelapsed = []
            for elapsed in self.times:
                self.allelapsed.append(elapsed)
            self.allelapsed.sort()
        return self.allelapsed

    def __str__(self):
        body = (
            self.hangs, self.hits(), self.total(), self.max(), self.min(),
            self.median(), self.mean(), self.url
            )
        return self.fmt % body

    def getheader(self):
        return self.fmt % ('Hangs', 'Hits', 'Total', 'Max', 'Min', 'Median',
                           'Mean', 'URL')
        
    fmt = "%5s %5s %5s %5s %5s %6s %5s %s"

    def hits(self):
        return len(self.times)
        
    def max(self):
        return max(self.all())
        
    def min(self):
        return min(self.all())
        
    def mean(self):
        l = len(self.times)
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
                if type(v1) is type('') or type(v2) is type(''): return "I"
                else: return (v1 + v2) / 2
    
    def total(self):
        t = 0
        all = self.all()
        for elapsed in all:
            if elapsed == "I": continue
            t = t + elapsed
        return t

def parsebigmlogline(line):
    tup = string.split(line, None, 3)
    if len(tup) == 3:
        code, id, timestr = tup
        return code, id, timestr, ''
    elif len(tup) == 4:
        return tup
    else:
        return None

def get_earliest_file_data(files):
    temp = {}
    earliest_fromepoch = 0
    earliest = None
    retn = None
    for file in files:
        line = file.readline()
        if not line:
            continue
        linelen = len(line)
        line = string.strip(line)
        tup = parsebigmlogline(line)
        if tup is None:
            print "Could not interpret line: %s" % line
            continue
        code, id, timestr, desc = tup
        timestr = string.strip(timestr)
        fromepoch = getdate(timestr)
        temp[file] = linelen
        if earliest_fromepoch == 0 or fromepoch < earliest_fromepoch:
            earliest_fromepoch = fromepoch
            earliest = file
            retn = [code, id, fromepoch, desc]

    for file, linelen in temp.items():
        if file is not earliest:
            file.seek(file.tell() - linelen)

    return retn

def get_requests(files, start=None, end=None, statsfname=None,
                 writestats=None, readstats=None):
    finished = []
    unfinished = {}
    if readstats:
        fp = open(statsfname, 'r')
        u = cPickle.Unpickler(fp)
        requests = u.load()
        fp.close()
        del u
        del fp
    else:
        while 1:
            tup = get_earliest_file_data(files)
            if tup is None:
                break
            code, id, fromepoch, desc = tup
            if start is not None and fromepoch < start: continue
            if end is not None and fromepoch > end: break
            if code == 'U':
                finished.extend(unfinished.values())
                unfinished.clear()
                request = StartupRequest()
                request.url = desc
                request.start = int(fromepoch)
                finished.append(request)
                continue
            request = unfinished.get(id)
            if request is None:
                if code != "B": continue # garbage at beginning of file
                request = Request()
                for pending_req in unfinished.values():
                    pending_req.active = pending_req.active + 1
                unfinished[id] = request
            t = int(fromepoch)
            try:
                request.put(code, t, desc)
            except:
                print "Unable to handle entry: %s %s %s"%(code, t, desc)
            if request.isfinished():
                del unfinished[id]
                finished.append(request)

        finished.extend(unfinished.values())
        requests = finished

        if writestats:
            fp = open(statsfname, 'w')
            p = cPickle.Pickler(fp)
            p.dump(requests)
            fp.close()
            del p
            del fp

    return requests

def analyze(requests, top, sortf, start=None, end=None, mode='cumulative',
            resolution=60, urlfocusurl=None, urlfocustime=60):

    if mode == 'cumulative':
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
        write(requests, top)
        
    elif mode=='timed':
        computed_start = requests[0].start
        computed_end = requests[-1].t_end
        if start and end:
            timewrite(requests,start,end,resolution)
        if start and not end:
            timewrite(requests,start,computed_end,resolution)
        if end and not start:
            timewrite(requests,computed_start,end,resolution)
        if not end and not start:
            timewrite(requests,computed_start,computed_end,resolution)

    elif mode == 'urlfocus':
        requests.sort(sortf)
        urlfocuswrite(requests, urlfocusurl, urlfocustime)
    
    else:
        requests.sort(sortf)
        write(requests, top)

def urlfocuswrite(requests, url, t):
    l = []
    i = 0
    for request in requests:
        if request.url == url: l.append(i)
        i = i + 1
    before = {}
    after = {}
    x = 0
    for n in l:
        x = x + 1
        r = requests[n]
        start = r.start
        earliest = start - t
        latest = start + t
        print 'URLs invoked %s seconds before and after %s (#%s, %s)' % \
              (t, url, x, r.shortprettystart())
        print '---'
        i = -1
        for request in requests:
            i = i + 1
            if request.start < earliest: continue
            if request.start > latest: break
            if n == i: # current request
                print '%3d' % (request.start - start),
                print '%s' % (request.shortprettystart()),
                print request.url
                continue
            if request.start <= start:
                if before.get(i):
                    before[i] = before[i] + 1
                else:
                    before[i] = 1
            if request.start > start:
                if after.get(i):
                    after[i] = after[i] + 1
                else:
                    after[i] = 1
            print '%3d' % (request.start - start),
            print '%s' % (request.shortprettystart()),
            print request.url
        print
    print ('Summary of URLs invoked before (and at the same time as) %s '
           '(times, url)' % url)
    before = before.items()
    before.sort()
    for k,v in before:
        print v, requests[k].url
    print
    print 'Summary of URLs invoked after %s (times, url)' % url
    after = after.items()
    after.sort()
    for k,v in after:
        print v, requests[k].url

def write(requests, top=0):
    if len(requests) == 0:
        print "No data.\n"
        return
    i = 0
    header = requests[0].getheader()
    print header
    for stat in requests:
        i = i + 1
        if verbose:
            print str(stat)
        else:
            print str(stat)[:78]
        if i == top:
            break

def getdate(val):
    try:
        val = string.strip(val)
        year, month, day = int(val[:4]), int(val[5:7]), int(val[8:10])
        hour,minute,second=int(val[11:13]),int(val[14:16]),int(val[17:19])
        t = time.mktime((year, month, day, hour, minute, second, 0, 0, -1))
        return t
    except:
        raise ProfileException, "bad date %s" % val

def getTimeslice(period, utime):
    low = int(math.floor(utime)) - period + 1
    high = int(math.ceil(utime)) + 1
    for x in range(low, high):
        if x % period == 0:
            return x

def timewrite(requests, start, end, resolution):
    print "Start: %s    End: %s   Resolution: %d secs" % \
        (tick2str(start), tick2str(end), resolution)
    print "-" * 78
    print
    print "Date/Time                #requests requests/second"

    d = {}
    max = 0
    min = None
    for r in requests:
        t = r.start
        slice = getTimeslice(resolution,t)
        if slice > max: max = slice
        if (min is None) or (slice < min): min = slice
        if d.has_key(slice):
            d[slice] = d[slice] + 1
        else:
            d[slice] = 1

    num = 0
    hits = 0
    avg_requests = None
    max_requests = 0
    for slice in range(min, max, resolution):
        num = d.get(slice, 0)
        if num>max_requests: max_requests = num
        hits = hits + num
        
        if avg_requests is None:
            avg_requests = num
        else:
            avg_requests = (avg_requests + num) / 2

        s = tick2str(slice)
        s = s + "     %6d         %4.2lf" % (num,num*1.0/resolution)
        print s 

    print '='*78 
    print " Peak:                  %6d         %4.2lf" % \
        (max_requests,max_requests*1.0/resolution)
    print "  Avg:                  %6d         %4.2lf" % \
        (avg_requests,avg_requests*1.0/resolution)
    print "Total:                  %6d          n/a " % (hits)
    
def tick2str(t):
    return time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(t))
    
def codesort(v1, v2):
    v1 = v1.endstage()
    v2 = v2.endstage()
    if v1 == v2:
        return 0
    
    if v1 == "B":
        return -1 # v1 is smaller than v2
    if v1 == "I":
        if v2 == "B": return 1 # v1 is larger than v2
        else: return -1
    if v1 == "A":
        if v2 in ['B', 'I']: return 1
        else: return -1
    if v1 == "E":
        return 1

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
    pname = sys.argv[0]
    details = details + """
Reports are of four types: cumulative, detailed, timed, or urlfocus.  The
default is cumulative. Data is taken from one or more Zope detailed request
logs (-M logs, aka 'big M' logs) or from a preprocessed statistics file.

For cumulative reports, each line in the profile indicates information
about a Zope method (URL) collected via a detailed request log.

For detailed reports, each line in the profile indicates information about
a single request.

For timed reports, each line in the profile indicates informations about
the number of requests and the number of requests/second for a period of time.

For urlfocus reports, ad-hoc information about requests surrounding the
specified url is given.

Each 'filename' is a path to a '-M' log that contains detailed request data.
Multiple input files can be analyzed at the same time by providing the path
to each file.  (Analyzing  multiple big M log files at once is useful if you
have more than one Zope client on a single machine and you'd like to
get an overview of all Zope activity on that machine).

If you wish to make multiple analysis runs against the same input data, you
may want to use the --writestats option.  The --writestats option creates a
file which holds preprocessed data representing the specfified input files.
Subsequent runs (for example with a different sort spec) will be much
faster if the  --readstats option is used to specify a preprocessed stats
file instead of actual input files because the logfile parse step is skipped.

If a 'sort' value is specified, sort the profile info by the spec.  The sort
order is descending unless indicated.    The default cumulative sort spec is
'total'.  The default detailed sort spec is 'start'.

For cumulative reports, the following sort specs are accepted:

  'hits'        -- the number of hits against the method
  'hangs'       -- the number of unfinished requests to the method
  'max'         -- the maximum time in secs taken by a request to this method
  'min'         -- the minimum time in secs taken by a request to this method
  'mean'        -- the mean time in secs taken by a request to this method
  'median'      -- the median time in secs taken by a request to this method
  'total'       -- the total time in secs across all requests to this method
  'url'         -- the URL/method name (ascending)

For detailed (non-cumulative) reports, the following sort specs are accepted:

  'start'       -- the start time of the request to ZServer (ascending)
  'win'         -- the num of secs ZServer spent waiting for input from client
  'wout'        -- the secs ZServer spent waiting for output from ZPublisher
  'wend'        -- the secs ZServer spent sending data to the client
  'total'       -- the secs taken for the request from begin to end
  'endstage'    -- the last successfully completed request stage (B, I, A, E)
  'osize'       -- the size in bytes of output provided by ZPublisher
  'httpcode'    -- the HTTP response code provided by ZPublisher (ascending)
  'active'      -- total num of requests pending at the end of this request
  'url'         -- the URL/method name (ascending)

For timed and urlfocus reports, there are no sort specs allowed.

If the 'top' argument is specified, only report on the top 'n' entries in
the profile (as per the sort). The default is to show all data in the profile.

If the 'verbose' argument is specified, do not trim url to fit into 80 cols.

If the 'today' argument is specified, limit results to hits received today.

The 'resolution' argument is used only for timed reports and specifies the
number of seconds between consecutive lines in the report 
(default is 60 seconds).

The 'urlfocustime' argument is used only for urlfocus reports and specifies the
number of seconds to target before and after the URL provided in urlfocus mode.
(default is 10 seconds).

If the 'start' argument is specified in the form 'DD/MM/YYYY HH:MM:SS' (UTC),
limit results to hits received after this date/time.

If the 'end' argument is specified in the form 'DD/MM/YYYY HH:MM:SS' (UTC),
limit results to hits received before this date/time.

'start' and 'end' arguments are not honored when request stats are obtained
via the --readstats argument.

Examples:

  %(pname)s debug.log

    Show cumulative report statistics for information in the file 'debug.log',
    by default sorted by 'total'.

  %(pname)s debug.log --detailed

    Show detailed report statistics sorted by 'start' (by default).

  %(pname)s debug.log debug2.log --detailed

    Show detailed report statistics for both logs sorted by 'start'
    (by default).

  %(pname)s debug.log --cumulative --sort=mean --today --verbose

    Show cumulative report statistics sorted by mean for entries in the log
    which happened today, and do not trim the URL in the resulting report.

  %(pname)s debug.log --urlfocus='/manage_main' --urlfocustime=60

    Show 'urlfocus' report which displays statistics about requests
    surrounding the invocation of '/manage_main'.  Focus on the time periods
    60 seconds before and after each invocation of the '/manage_main' URL.
    
  %(pname)s debug.log --detailed --start='2001/05/10 06:00:00'
    --end='2001/05/11 23:00:00'

    Show detailed report statistics for entries in 'debug.log' which
    begin after 6am UTC on May 10, 2001 and which end before
    11pm UTC on May 11, 2001.

  %(pname)s debug.log --timed --resolution=300 --start='2001/05/10 06:00:00'
    --end='2001/05/11 23:00:00'

    Show timed report statistics for entries in the log for one day
    with a resolution of 5 minutes

  %(pname)s debug.log --top=100 --sort=max

    Show cumulative report of the the 'top' 100 methods sorted by maximum
    elapsed time.

  %(pname)s debug.log debug2.log --writestats='requests.stat'

    Write stats file for debug.log and debug2.log into 'requests.stat' and
    show default report.

  %(pname)s --readstats='requests.stat' --detailed

    Read from 'requests.stat' stats file (instead of actual -M log files)
    and show detailed report against this data.""" % {'pname':pname}
    return details

def usage(basic=1):
    usage = (
        """
Usage: %s filename1 [filename2 ...]
          [--cumulative | --detailed | [--timed --resolution=seconds]]
          [--sort=spec]
          [--top=n]
          [--verbose]
          [--today | [--start=date] [--end=date] ]
          [--writestats=filename | --readstats=filename]
          [--urlfocus=url]
          [--urlfocustime=seconds]
          [--help]
        
Provides a profile of one or more Zope "-M" request log files.
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
    mode = 'cumulative'
    sortby = None
    trim = 0
    top = 0
    verbose = 0
    start = None
    end = None
    resolution=60
    urlfocustime=10
    urlfocusurl=None
    statsfname = None
    readstats = 0
    writestats = 0
    
    files = []
    i = 1
    for arg in sys.argv[1:]:
        if arg[:2] != '--':
            files.append(open(arg))
            sys.argv.remove(arg)
            i = i + 1

    try:
        opts, extra = getopt.getopt(
            sys.argv[1:], '', ['sort=', 'top=', 'help', 'verbose', 'today',
                               'cumulative', 'detailed', 'timed','start=',
                               'end=','resolution=', 'writestats=',
                               'readstats=','urlfocus=','urlfocustime=']
            )
        for opt, val in opts:
            if opt=='--readstats':
                statsfname = val
                readstats = 1
            elif opt=='--writestats':
                statsfname = val
                writestats = 1
            if opt=='--sort': sortby = val
            if opt=='--top': top=int(val)
            if opt=='--help': print detailedusage(); sys.exit(0)
            if opt=='--verbose':
                verbose = 1
            if opt=='--resolution':
                resolution=int(val)
            if opt=='--today':
                now = time.localtime(time.time())
                # for testing - now = (2001, 04, 19, 0, 0, 0, 0, 0, -1)
                start = list(now)
                start[3] = start[4] = start[5] = 0
                start = time.mktime(start)
                end = list(now)
                end[3] = 23; end[4] = 59; end[5] = 59
                end = time.mktime(end)
            if opt=='--start':
                start = getdate(val)
            if opt=='--end':
                end = getdate(val)
            if opt=='--detailed':
                mode='detailed'
                d_sortby = sortby
            if opt=='--cumulative':
                mode='cumulative'
            if opt=='--timed':
                mode='timed'
            if opt=='--urlfocus':
                mode='urlfocus'
                urlfocusurl = val
            if opt=='--urlfocustime':
                urlfocustime=int(val)

        validcumsorts = ['url', 'hits', 'hangs', 'max', 'min', 'median',
                         'mean', 'total']
        validdetsorts = ['start', 'win', 'wout', 'wend', 'total',
                         'endstage', 'isize', 'osize', 'httpcode',
                         'active', 'url']

        if mode == 'cumulative':
            if sortby is None: sortby = 'total'
            assert sortby in validcumsorts, (sortby, mode, validcumsorts)
            if sortby in ['url']:
                sortf = Sort(sortby, ascending=1)
            else:
                sortf = Sort(sortby)
        elif mode == 'detailed':
            if sortby is None: sortby = 'start'
            assert sortby in validdetsorts, (sortby, mode, validdetsorts)
            if sortby in ['start', 'url', 'httpcode']:
                sortf = Sort(sortby, ascending=1)
            elif sortby == 'endstage':
                sortf = codesort
            else:
                sortf = Sort(sortby)
        elif mode=='timed':
            sortf = None
        elif mode=='urlfocus':
            sortf = Sort('start', ascending=1)
        else:
            raise 'Invalid mode'

        req=get_requests(files, start, end, statsfname, writestats, readstats)
        analyze(req, top, sortf, start, end, mode, resolution, urlfocusurl,
                urlfocustime)

    except AssertionError, val:
        a = "%s is not a valid %s sort spec, use one of %s"
        print a % (val[0], val[1], val[2])
        sys.exit(0)
    except getopt.error, val:
        print val
        sys.exit(0)
    except ProfileException, val:
        print val
        sys.exit(0)
    except SystemExit:
        sys.exit(0)
    except:
        import traceback
        traceback.print_exc()
        print usage()
        sys.exit(0)
