import time, sys, string, os


_stupid_dest=None
_no_stupid_log=[]
format_exception_only=None


# Standard severities
BLATHER=-100
INFO=0      
PROBLEM=WARNING=100             
ERROR=200   
PANIC=300

def severity_string(severity, mapping={
    -100: 'BLATHER',
    0: 'INFO',       
    100: 'PROBLEM', 
    200: 'ERROR',    
    300: 'PANIC', 
    }):
    """Convert a severity code to a string
    """
    s=int(severity)
    if mapping.has_key(s): s=mapping[s]
    else: s=''
    return "%s(%s)" % (s, severity)


class stupidFileLogger:

    """ a stupid File Logger """


    def __init__(self):
        pass

    def __call__(self, sub, sev, sum, det, err):
        stupid_log_write(sub, sev, sum, det, err)



def stupid_log_write(subsystem, severity, summary, detail, error):
    if severity < 0: return

    global _stupid_dest
    if _stupid_dest is None:
        if os.environ.has_key('STUPID_LOG_FILE'):
            f=os.environ['STUPID_LOG_FILE']
            if f: _stupid_dest=open(f,'a')
            else: _stupid_dest=sys.stderr
        elif os.environ.get('Z_DEBUG_MODE',0):
            _stupid_dest=sys.stderr
        else:
            _stupid_dest=_no_stupid_log

    if _stupid_dest is _no_stupid_log: return

    _stupid_dest.write(
        "------\n"
        "%s %s %s %s\n%s"
        %
        (log_time(),
         severity_string(severity),
         subsystem,
         summary,
         detail,
         )
        )



    _stupid_dest.flush()

    if error:
        try:
            _stupid_dest.write(format_exception(
                error[0], error[1], error[2],
                trailer='\n', limit=100))
        except:
            _stupid_dest.write("%s: %s\n" % error[:2])


def format_exception(etype,value,tb,limit=None, delimiter='\n',
                     header='', trailer=''):
    global format_exception_only
    if format_exception_only is None:
        import traceback
        format_exception_only=traceback.format_exception_only

    result=['Traceback (innermost last):']
    if header: result.insert(0,header)
    if limit is None:
        if hasattr(sys, 'tracebacklimit'):
            limit = sys.tracebacklimit
    n = 0
    while tb is not None and (limit is None or n < limit):
        f = tb.tb_frame
        lineno = tb.tb_lineno
        co = f.f_code
        filename = co.co_filename
        name = co.co_name
        locals=f.f_locals
        result.append('  File %s, line %d, in %s'
                      % (filename,lineno,name))
        try: result.append('    (Object: %s)' %
                           locals[co.co_varnames[0]].__name__)
        except: pass
        try: result.append('    (Info: %s)' %
                           str(locals['__traceback_info__']))
        except: pass
        tb = tb.tb_next
        n = n+1
    result.append(string.join(format_exception_only(etype, value),
                       ' '))
    if trailer: result.append(trailer)

    return string.join(result, delimiter)


def log_time():
    """Return a simple time string without spaces suitable for logging
    """
    return ("%4.4d-%2.2d-%2.2dT%2.2d:%2.2d:%2.2d"
            % time.gmtime(time.time())[:6])






