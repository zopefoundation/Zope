# -*- Mode: Python; tab-width: 4 -*-

# demo of bobo-like persistent script handler
# how this is different from CGI:
# rather than passing request info in the 'environment',
# we give the 'main' function direct access to the medusa
# request object.

# stdin, stdout, and stderr all act in a cgi-ish fashion.
# [i.e, form/put/post data can be found on stdin, use the
#  cgi module to handle forms...]

# some quick persistence comments:
# You can add a command URI that will reload the module
#   if you need to.  You might also change persistent_script_handler
#   to automatically reload a module if it's changed on disk.
# You can preserve data across a reload.  Using 'count' as
#   an example, replace the line below with:
#   try:
#     count
#   except NameError;
#     count = 0
#   

count = 0

import string

def html_clean (s):
    s = string.replace (s, '<', '&lt;')
    s = string.replace (s, '>', '&gt;')
    return s
    
def main (request):
    global count
    count = count + 1
    print '<html><h1>Hit Count=%d</h1>' % count
    print '<h3>Request Attributes:</h3><ul>'
    print '<li>command : %s'	% request.command
    print '<li>uri: %s'			% html_clean (request.uri)
    print '<li>channel: %s'		% html_clean (repr (request.channel))
    print '</ul>'
    print '</html>'
