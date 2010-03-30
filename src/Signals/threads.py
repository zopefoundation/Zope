import sys
import thread
import traceback
import time
from cStringIO import StringIO


def dump_threads():
    """Dump running threads. Returns a string with the tracebacks."""

    frames = sys._current_frames()
    this_thread_id = thread.get_ident()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    res = ["Threads traceback dump at %s\n" % now]
    for thread_id, frame in frames.iteritems():
        if thread_id == this_thread_id:
            continue

        # Find request in frame
        reqinfo = ''
        f = frame
        while f is not None:
            co = f.f_code
            if co.co_name == 'publish':
                if co.co_filename.endswith('/ZPublisher/Publish.py'):
                    request = f.f_locals.get('request')
                    if request is not None:
                        reqinfo += (request.get('REQUEST_METHOD', '') + ' ' +
                                   request.get('PATH_INFO', ''))
                        qs = request.get('QUERY_STRING')
                        if qs:
                            reqinfo += '?'+qs
                    break
            f = f.f_back
        if reqinfo:
            reqinfo = " (%s)" % reqinfo

        output = StringIO()
        traceback.print_stack(frame, file=output)
        res.append("Thread %s%s:\n%s" %
            (thread_id, reqinfo, output.getvalue()))

    frames = None
    res.append("End of dump")
    return '\n'.join(res)
