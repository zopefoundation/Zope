##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Convert an http tcpwatch session to a doctest

$Id: dochttp.py,v 1.2 2004/10/21 21:19:09 shh42 Exp $
"""

import errno
import optparse
import os
import re
import rfc822
import sys

usage = """usage: %prog <options> directory

Convert an http tcpwatch recorded sesssion to a doctest file, which is
written to standard output.

"""

parser = optparse.OptionParser(usage)
parser.add_option("-p", "--prefix", default="watch",
                  help="Prefix for recorded tcpwatch session files")
parser.add_option("-U", "--skip-url", action="append",
                  help="Regular expression for URLs to skip")
parser.add_option("-E", "--skip-extension", action="append",
                  help="URL file-extension to skip")
parser.add_option("-e", "--extension", action="append",
                  help="URL file-extension to include")
parser.add_option("-I", "--skip-request-header", action="append",
                  help="Request header to skip")
parser.add_option("-O", "--skip-response-header", action="append",
                  help="Response header to skip")
parser.add_option("-r", "--clean-redirects", action="store_true",
                  help="Strip content from redirect responses",
                  default=False)

default_options = [
    '-e', 'html',

    '-I', 'Accept-Charset', '-I', 'Accept-Encoding', '-I', 'Accept-Language',
    '-I', 'Accept', '-I', 'Connection', '-I', 'Host', '-I', 'Keep-Alive',
    '-I', 'User-Agent',

    '-O', 'Date', '-O', 'Server', '-O', 'X-Content-Type-Warning',
    '-O', 'X-Powered-By',

    ]

def dochttp(args=sys.argv[1:], default=None):
    """Convert a tcpwatch recorded sesssion to a doctest file"""
    if default is None:
        default = default_options

    options, args = parser.parse_args(default+args)
    try:
        directory, = args
    except:
        parser.print_help()
        sys.exit(1)

    skip_extensions = options.skip_extension or ()
    extensions = [ext for ext in (options.extension or ())
                  if ext not in skip_extensions]
    skip_urls = [re.compile(pattern) for pattern in (options.skip_url or ())]

    names = [name[:-len(".request")]
             for name in os.listdir(directory)
             if name.startswith(options.prefix) and name.endswith('.request')
             ]
    names.sort()

    extre = re.compile("[.](\w+)$")

    for name in names:
        requests =  Requests(
                        open(os.path.join(directory, name + ".request"), 'rb'),
                        options.skip_request_header,
                        )
        responses = Responses(
                        open(os.path.join(directory, name + ".response"), 'rb'),
                        options.skip_response_header,
                        )

        # We use map so as *not* to truncate at shortest input.
        # We want an error if the number of requests and responses
        # is different.
        for request, response in map(None, requests, responses):
            assert (request and response) or not (request or response)

            path = request.path
            ext = extre.search(path)
            if ext:
                ext = ext.group(1)
                if extensions:
                    if ext not in extensions:
                        continue
                else:
                    if ext in skip_extensions:
                        continue
            
            for skip_url in skip_urls:
                if skip_url.search(request.path):
                    break
            else:
                try:
                    output_test(request, response, options.clean_redirects)
                except IOError, e:
                    if e.errno == errno.EPIPE:
                        return
                    raise
    

def output_test(request, response, clean_redirects=False):
    print
    print
    print '  >>> print http(r"""'
    print '  ...', '\n  ... '.join(request.lines())+'""")'
    if response.code in (301, 302, 303) and clean_redirects:
        if response.headers:
            for i in range(len(response.headers)):
                h, v = response.headers[i]
                if h == "Content-Length":
                    response.headers[i] = (h, "...")
        lines = response.header_lines()
        if lines:
            lines.append("...")
    else:
        lines = response.lines()
    print ' ', '\n  '.join([line.rstrip() and line or '<BLANKLINE>'
                             for line in lines])

class Message:

    start = ''

    def __init__(self, file, skip_headers):
        start = file.readline().rstrip()
        if start:
            self.start = start
            if start.startswith("HTTP/"):
                # This is a response; extract the response code:
                self.code = int(start.split()[1])
            headers = [split_header(header)
                       for header in rfc822.Message(file).headers
                       ]
            headers = [
                ('-'.join([s.capitalize() for s in name.split('-')]),
                 v.rstrip()
                 )
                for (name, v) in headers
                if name.lower() not in skip_headers
            ]
            self.headers = headers
            content_length = int(dict(headers).get('Content-Length', '0'))
            if content_length:
                self.body = file.read(content_length).split('\n')
            else:
                self.body = []

    def __nonzero__(self):
        return bool(self.start)

    def lines(self):
        output = self.header_lines()
        if output:
            output.extend(self.body)
        return output

    def header_lines(self):
        if self.start:
            output = [self.start]
            headers = ["%s: %s" % (name, v) for (name, v) in self.headers]
            headers.sort()
            output.extend(headers)
            output.append('')
        else:
            output = []
        return output

headerre = re.compile('(\S+): (.+)$')
def split_header(header):
    return headerre.match(header).group(1, 2)

def messages(cls, file, skip_headers):
    skip_headers = [name.lower() for name in (skip_headers or ())]
    while 1:
        message = cls(file, skip_headers)
        if message:
            yield message
        else:
            break
        
class Request(Message):

    path = ''
    
    def __init__(self, file, skip_headers):
        Message.__init__(self, file, skip_headers)
        if self.start:
            self.command, self.path, self.protocol = self.start.split()
    
def Requests(file, skip_headers):
    return messages(Request, file, skip_headers)
    
def Responses(file, skip_headers):
    return messages(Message, file, skip_headers)

main = dochttp

if __name__ == '__main__':
    main()
