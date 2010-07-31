##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
"""Yet another lag analysis tool
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

class Times:

    tid = 1l

    def __init__(self):
        self.times = []
        self.hangs = 0
        Times.tid += 1
        self.tid = Times.tid # generate a unique id

    def finished(self, request):
        self.times.append(request.app_seconds)

    def hung(self):
        self.hangs += 1

    def impact(self):
        times = self.times
        if not times:
            self.median = self.mean = self.impact = 0
            return 0
        self.times.sort()
        n = len(times) 
        if n % 2:
            m = times[(n+1)/2-1]
        else:
            m = .5 * (times[n/2]+times[n/2-1])
        self.median = m
        self.mean = sum(times)/n
        self.impact = self.mean * (n+self.hangs)
        return self.impact

    def __str__(self):
        times = self.times
        if not times:
            return "              0                             %5d" % (
                self.hangs)
            
        n = len(times)
        m = self.median
        return "%9.1f %5d %6.0f %6.2f %6.2f %6.0f %5d" % (
            self.impact, n, times[0], m, self.mean, times[-1], self.hangs)

    def html(self):
        times = self.times
        if not times:
            print td('', 0, '', '', '', '', self.hangs)
        else:
            n = len(times)
            m = self.median
            impact = '<a name="u%s">%s' % (self.tid, self.impact)
            print td(impact, n, times[0], m, self.mean, times[-1],
                     self.hangs)

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

    if options.html:
        print_app_requests = print_app_requests_html
        output_minute = output_minute_html
        output_stats = output_stats_html
        minutes_header = minutes_header_html
        minutes_footer = minutes_footer_html
        print '<html title="trace log statistics"><body>'
    else:
        print_app_requests = print_app_requests_text
        output_minute = output_minute_text
        output_stats = output_stats_text
        minutes_header = minutes_header_text
        minutes_footer = minutes_footer_text
        
        
    urls = {}
    [file] = args
    lmin = ldt = None
    requests = {}
    input = apps = output = n = 0
    spr = spa = 0.0
    restart = restarts.pop(0)
    minutes_header()
    remove_prefix = options.remove_prefix
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
                               urls,
                               "\nLeft over:")
            record_hung(urls, requests)
            requests = {}
            input = apps = output = n = 0
            spr = spa = 0.0
            restart = restarts.pop(0)
        ldt = dt
        
        if min != lmin:
            if lmin is not None:
                output_minute(lmin, requests, input, apps, output, n, spr, spa)
                if apps > options.apps:
                    print_app_requests(requests, dt,
                                       options.old_requests,
                                       options.app_requests,
                                       urls,
                                       )
            lmin = min
            spr = 0.0
            spa = 0.0
            n = 0
            
        if typ == 'B':
            if rid in requests:
                request = requests[rid]
                if request.state == 'output':
                    output -= 1
                elif request.state == 'app':
                    apps -= 1
                else:
                    input -= 1
            
            input += 1
            request = Request(dt, *record[3:5])
            if remove_prefix and request.url.startswith(remove_prefix):
                request.url = request.url[len(remove_prefix):]
            requests[rid] = request
            times = urls.get(request.url)
            if times is None:
                times = urls[request.url] = Times()
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
                times = urls[request.url]
                times.finished(request)
        else:
            print 'WTF', record

    print_app_requests(requests, dt,
                       options.old_requests,
                       options.app_requests,
                       urls,
                       "Left over:")

    minutes_footer()

    output_stats(urls)

    if options.html:
        print '</body></html>'

def output_stats_text(urls):
    print
    print 'URL statistics:'
    print "   Impact count    min median   mean    max hangs"
    print "========= ===== ====== ====== ====== ====== ====="
    urls = [(times.impact(), url, times)
            for (url, times) in urls.iteritems()
            ]
    urls.sort()
    urls.reverse()
    for (_, url, times) in urls:
        if times.impact > 0 or times.hangs:
            print times, url

def output_stats_html(urls):
    print
    print 'URL statistics:'
    print '<table border="1">'
    print '<tr><th>Impact</th><th>count</th><th>min</th>'
    print     '<th>median</th><th>mean</th><th>max</th><th>hangs</th></tr>'
    urls = [(times.impact(), url, times)
            for (url, times) in urls.iteritems()
            ]
    urls.sort()
    urls.reverse()
    for (_, url, times) in urls:
        if times.impact > 0 or times.hangs:
            print '<tr>'
            times.html()
            print td(url)
            print '</tr>'
    print '</table>'

def minutes_header_text():
    print
    print "          minute   req input   app output"
    print "================ ===== ===== ===== ======"

def minutes_footer_text():
    print

def minutes_header_html():
    print '<table border="2">'
    print "<tr>"
    print '<th>Minute</th>'
    print '<th>Requests</th>'
    print '<th>Requests inputing</th>'
    print '<th>Requests executing or waiting</th>'
    print '<th>Requests outputing</th>'
    print '<th>Requests completed</th>'
    print '<th>Mean Seconds Per Request Total</th>'
    print '<th>Mean Seconds Per Request in App</th>'
    print "</tr>"

def minutes_footer_html():
    print '</table>'

def output_minute_text(lmin, requests, input, apps, output, n, spr, spa):
    print lmin.replace('T', ' '), "%5d I=%3d A=%3d O=%5d " % (
        len(requests), input, apps, output),
    if n:
        print "N=%4d %10.2f %10.2f" % (n, spr/n, spa/n)
    else:
        print

def td(*values):
    return ''.join([("<td>%s</td>" % s) for s in values])

def output_minute_html(lmin, requests, input, apps, output, n, spr, spa):
    print '<tr>'
    apps = '<font size="+2"><strong>%s</strong></font>' % apps
    print td(lmin.replace('T', ' '), len(requests), input, apps, output)
    if n:
        print td(n, "%10.2f" % (spr/n), "%10.2f" % (spa/n))
    print '</tr>'

def find_restarts(event_log):
    result = []
    for l in open(event_log):
        if l.strip().endswith("Zope Ready to handle requests"):
            result.append(parsedt(l.split()[0]))
    return result

def record_hung(urls, requests):
    for request in requests.itervalues():
        times = urls.get(request.url)
        if times is None:
            times = urls[request.url] = Times()
        times.hung()

def print_app_requests_text(requests, dt, min_seconds, max_requests, urls,
                       label=''):
    requests = [
        ((dt-request.input_time).seconds, request)
        for request in requests.values()
        if request.state == 'app'
    ]

    urls = {}
    for s, request in requests:
        urls[request.url] = urls.get(request.url, 0) + 1
    
    requests.sort()
    requests.reverse()
    for s, request in requests[:max_requests]:
        if s < min_seconds:
            continue
        if label:
            print label
            label = ''
        url = request.url
        repeat = urls[url]
        if repeat > 1:
            print s, "R=%d" % repeat, url
        else:
            print s, url

def print_app_requests_html(requests, dt, min_seconds, max_requests, allurls,
                            label=''):
    requests = [
        ((dt-request.input_time).seconds, request)
        for request in requests.values()
        if request.state == 'app'
    ]

    urls = {}
    for s, request in requests:
        urls[request.url] = urls.get(request.url, 0) + 1
    
    requests.sort()
    requests.reverse()
    printed = False
    for s, request in requests[:max_requests]:
        if s < min_seconds:
            continue
        if label:
            print label
            label = ''
        if not printed:
            minutes_footer_html()
            print '<table border="1">'
            print '<tr><th>age</th><th>R</th><th>url</th></tr>'
            printed = True
        url = request.url
        repeat = urls[url]
        print '<tr>'
        if repeat <= 1:
            repeat = ''
        url = '<a href="#u%s">%s</a>' % (allurls[url].tid, url)
        print td(s, repeat, url)
        print '</tr>'

    if printed:
        print '</table>'
        minutes_header_html()

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
parser.add_option("--html", dest='html', action='store_true',
                  help="""
Generate HTML output.
""")
parser.add_option("--remove-prefix", dest='remove_prefix',
                  help="""
A prefex to be removed from URLS.
""")
                  

            
if __name__ == '__main__':
    main()
