import getopt

def getOptionDescriptions():
    """ Temporary implementation """

    short, long = getOptions()
    n = 0
    short_d = {}
    long_d = {}

    last = 0
    n = 0

    print short

    if short:
        while 1:
            try:
                opt = short[n]
            except IndexError:
                next = None
            try:
                next = short[n+1]
            except IndexError:
                next = None
            if next == ':':
                short_d[opt] = 1
                n = n + 2
            else:
                if next is None and short.endswith(':'):
                    short_d[opt] = 1
                else:
                    short_d[opt] = 0
                n = n + 1
            if next is None:
                break

    for opt in long:
        if opt.endswith('='):
            long_d[opt[:-1]] = 1
        else:
            long_d[opt] = 0

    opts = []

    short_l = short_d.items()
    short_l.sort()
    for k, v in short_l:
        opts.append('    -%s%s' % (k, (v and ' <value>' or '')))

    long_l = long_d.items()
    long_l.sort()
    for k, v in long_l:
        opts.append('    --%s%s' % (k, (v and ' <value>' or '')))
    return '\n'.join(opts)

def getOptions():
    short = 'Z:t:i:D:a:d:u:L:l:M:E:Xw:W:f:p:F:m:'
    long  = [
             'zserver-threads=',
             'python-check-interval=',
             'debug-mode=',
             'ip-address=',
             'dns-ip-address=',
             'effective-user=',
             'locale=',
             'access-log=',
             'trace-log=',
             'event-log=',
             'disable-servers',
             'http-server=',
             'webdav-source-server=',
# XXX need to finish these
#             'ftp-server=',
#             'pcgi-server=',
#             'fcgi-server=',
#             'monitor-server=',
#             'icp-server=',
             ]
    return short, long

class CommandLineOptions:

    def __call__(self, cfg, options):
        import Zope.Startup.datatypes
        import Zope.Startup.handlers
        import ZConfig.datatypes

        short, long = getOptions()
        opts, args = getopt.getopt(options, short, long)

        for k, v in opts:
            # set up data that servers may rely on
            if k in ('-t', '--zserver-threads'):
                cfg.zserver_threads = int(v)
            elif k in ('-i', '--python-check-interval'):
                cfg.python_check_interval = int(v)
            elif k in ('-D', '--debug-mode'):
                datatype = ZConfig.datatypes.asBoolean
                handler = Zope.Startup.handlers.debug_mode
                v = datatype(v)
                handler(v)
                cfg.debug_mode = v
            elif k in ('-i', '--ip-address'):
                datatype = ZConfig.datatypes.IpaddrOrHostname()
                cfg.ip_address = datatype(v)
            elif k in ('-d', '--dns-ip-address'):
                datatype = ZConfig.datatypes.IpaddrOrHostname()
                cfg.dns_ip_address = datatype(v)
            elif k in ('-u', '--effective-user'):
                cfg.effective_user = v
            elif k in ('-L', '--locale'):
                datatype = ZConfig.datatypes.check_locale
                cfg.locale = datatype(v)
            elif k in ('-l', '--access-log'):
                cfg.access = default_logger('access', v,
                                            '%(message)s',
                                            '%Y-%m-%dT%H:%M:%S')
            elif k in ('-M', '--trace-log'):
                cfg.trace = default_logger('trace', v,
                                           '%(message)s',
                                           '%Y-%m-%dT%H:%M:%S')
            elif k in ('-E', '--event-log'):
                cfg.trace = default_logger('event', v,
                                           '------\n%(asctime)s %(message)s',
                                           '%Y-%m-%dT%H:%M:%S')
            elif k in ('-X', '--disable-servers'):
                cfg.servers = []
            else:
                # continue if we've not matched, otherwise
                # fall through to the pop statement below
                continue

            opts.pop(0) # pop non-server data from opts

        factory = Zope.Startup.handlers.ServerFactoryFactory(cfg)

        for k, v in opts:
            # set up server data from what's left in opts,
            # using repopulated cfg
            if k in ('-w', '--http-server'):
                datatype = ZConfig.datatypes.inet_address
                host, port = datatype(v)
                section = dummy()
                section.ports = [(host, port)]
                section.force_connection_close = 0
                cfg.servers.append(['http_server',
                                    factory.http_server(section)[0]])
            if k in ('-W', '--webdav-source-server'):
                datatype = ZConfig.datatypes.inet_address
                host, port = datatype(v)
                section = dummy()
                section.ports = [(host, port)]
                section.force_connection_close = 0
                cfg.servers.append(['webdav_source_server',
                                    factory.webdav_source_server(section)[0]])

class dummy:
    # used as a namespace generator
    pass
            
def default_logger(name, file, format, dateformat):
    import Zope.Startup.datatypes
    logger = dummy()
    logger.level = 20
    handler = dummy()
    handler.file = file
    handler.format = format
    handler.dateformat = dateformat
    handler.level = 20
    handlers = [Zope.Startup.datatypes.file_handler(handler)]
    return Zope.Startup.datatypes.LoggerWrapper(name, 20, handlers)
