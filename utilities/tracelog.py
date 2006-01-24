##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Yet another trace log analysis tool

$Id$
"""

import datetime, optparse, sys



class Request:

    output_bytes = '-'

    def __init__(self, start, method, url):
        self.method = method
        self.url = url
        self.start = start
        self.state = 'input'

    def I(self, input_time, input_bytes):
        self.input_time = input_time
        self.input_bytes = input_bytes
        self.state = 'app'

    def A(self, app_time, response, output_bytes):
        self.app_time = app_time
        self.response = response
        self.output_bytes = output_bytes
        self.state = 'output'

    def E(self, end):
        self.end = end

    @property
    def app_seconds(self):
        return (self.app_time - self.input_time).seconds

    @property
    def total_seconds(self):
        return (self.end - self.start).seconds

def parsedt(s):
    date, time = s.split('T')
    return datetime.datetime(*(
        map(int, date.split('-')) 
        +
        map(int, time.split(':'))         
        ))

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    options, args = parser.parse_args(args)
    if options.event_log:
        restarts = find_restarts(options.event_log)
    else:
        restarts = []
        
    restarts.append(datetime.datetime.utcnow()+datetime.timedelta(1000))

    [file] = args
    lmin = ldt = None
    requests = {}
    input = apps = output = n = 0
    spr = spa = 0.0
    restart = restarts.pop(0)
    for record in open(file):
        record = record.split()
        typ, rid, dt = record[:3]
        min = dt[:-3]
        dt = parsedt(dt)
        if dt == restart:
            continue
        while dt > restart:
            print_app_requests(requests, ldt,
                               options.old_requests,
                               options.app_requests,
                               "\nLeft over:")
            requests = {}
            input = apps = output = n = 0
            spr = spa = 0.0
            restart = restarts.pop(0)
        ldt = dt
        
        if min != lmin:
            if lmin is not None:
                
                print lmin.replace('T', ' '), "%4d I=%3d A=%3d O=%3d " % (
                    len(requests), input, apps, output),
                if n:
                    print "N=%4d %10.2f %10.2f" % (n, spr/n, spa/n)
                else:
                    print

                if apps > options.apps:
                    print_app_requests(requests, dt,
                                       options.old_requests,
                                       options.app_requests,
                                       )
            lmin = min
            spr = 0.0
            spa = 0.0
            n = 0
            
        if typ == 'B':
            input += 1
            requests[rid] = Request(dt, *record[3:5])
        elif typ == 'I':
            if rid in requests:
                input -= 1
                apps += 1
                requests[rid].I(dt, record[3])
        elif typ == 'A':
            if rid in requests:
                apps -= 1
                output += 1
                requests[rid].A(dt, *record[3:5])
        elif typ == 'E':
            if rid in requests:
                output -= 1
                request = requests.pop(rid)
                request.E(dt)
                spr += request.total_seconds
                spa += request.app_seconds
                n += 1
        else:
            print 'WTF', record

    print_app_requests(requests, dt,
                       options.old_requests,
                       options.app_requests,
                       "Left over:")

def find_restarts(event_log):
    result = []
    for l in open(event_log):
        if l.strip().endswith("Zope Ready to handle requests"):
            result.append(parsedt(l.split()[0]))
    return result

def print_app_requests(requests, dt, min_seconds, max_requests, label=''):
    requests = [
        ((dt-request.input_time).seconds, request)
        for request in requests.values()
        if request.state == 'app'
    ]
    requests.sort()
    requests.reverse()
    for s, request in requests[:max_requests]:
        if s < min_seconds:
            continue
        if label:
            print label
            label = ''
        print s, request.url

parser = optparse.OptionParser("""
Usage: %prog [options] trace_log_file

Output trace log data showing:

- number of active requests,
- number of input requests (requests gathering input),
- number of application requests,
- number of output requests,
- number of requests completed in the minute shown,
- mean seconds per request and
- mean application seconds per request.

Note that we don't seem to be logging when a connection to the client
is broken, so the number of active requests, and especially the number
of outputing requests tends to grow over time. This is spurious.

Also, note that, unfortunately, application requests include requests
that are running in application threads and requests waiting to get an
application thread.

When application threads get above the app request threshold, then we
show the requests that have been waiting the longest.

""")

parser.add_option("--app-request-threshold", "-a", dest='apps',
                  type="int", default=10,
                  help="""
Number of pending application requests at which detailed request information
if printed.
""")
parser.add_option("--app-requests", "-r", dest='app_requests',
                  type="int", default=10,
                  help="""
How many requests to show when the maximum number of pending
apps is exceeded.
""")
parser.add_option("--old-requests", "-o", dest='old_requests',
                  type="int", default=10,
                  help="""
Number of seconds beyond which a request is considered old.
""")
parser.add_option("--event-log", "-e", dest='event_log',
                  help="""
The name of an event log that goes with the trace log.  This is used
to determine when the server is restarted, so that the running trace data structures can be reinitialized.
""")
                  

            
if __name__ == '__main__':
    main()
