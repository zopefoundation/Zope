import os
import types

from misc.factory import Factory

# top-level key handlers

def _setenv(name, value):
    if isinstance(value, types.StringTypes):
        os.environ[name] = value
    else:
        os.environ[name] = `value`

def _append_slash(value):
    if value is None:
        return None
    if not value.endswith(os.sep):
        return value + os.sep
    return value

def software_home(value):
    value = _append_slash(value)
    value and _setenv('SOFTWARE_HOME', value)
    return value

def zope_home(value):
    value = _append_slash(value)
    value and _setenv('ZOPE_HOME', value)
    return value

def instance_home(value):
    value = _append_slash(value)
    value and _setenv('INSTANCE_HOME', value)
    return value

def client_home(value):
    value = _append_slash(value)
    value and _setenv('CLIENT_HOME', value)
    return value

def debug_mode(value):
    value and _setenv('Z_DEBUG_MODE', '1')
    return value

def enable_product_installation(value):
    value and _setenv('FORCE_PRODUCT_LOAD', '1')
    return value

def locale(value):
    import locale
    locale.setlocale(locale.LC_ALL, value)
    return value

def use_daemon_process(value):
    value and _setenv('Z_DEBUG_MODE', '1')
    return value

def zserver_read_only_mode(value):
    value and _setenv('ZOPE_READ_ONLY', '1')
    return value

def automatically_quote_dtml_request_data(value):
    not value and _setenv('ZOPE_DTML_REQUEST_AUTOQUOTE', '0')
    return value

def skip_authentication_checking(value):
    value and _setenv('ZSP_AUTHENTICATED_SKIP', '1')
    return value

def skip_ownership_checking(value):
    value and _setenv('ZSP_OWNEROUS_SKIP', '1')
    return value

def maximum_number_of_session_objects(value):
    default = 1000
    value not in (None, default) and _setenv('ZSESSION_OBJECT_LIMIT', value)
    return value

def session_add_notify_script_path(value):
    value is not None and _setenv('ZSESSION_ADD_NOTIFY', value)
    return value

def session_delete_notify_script_path(value):
    value is not None and _setenv('ZSESSION_DEL_NOTIFY', value)
    return value

def session_timeout_minutes(value):
    default = 20
    value not in (None, default) and _setenv('ZSESSION_TIMEOUT_MINS', value)
    return value

def suppress_all_access_rules(value):
    value and _setenv('SUPPRESS_ACCESSRULE', value)
    return value

def suppress_all_site_roots(value):
    value and _setenv('SUPPRESS_SITEROOT', value)
    return value

def database_quota_size(value):
    value and _setenv('ZOPE_DATABASE_QUOTA', value)
    return value

def read_only_database(value):
    value and _setenv('ZOPE_READ_ONLY', '1')
    return value

def zeo_client_name(value):
    value and _setenv('ZEO_CLIENT', value)
    return value

def structured_text_header_level(value):
    value is not None and _setenv('STX_DEFAULT_LEVEL', value)
    return value

def maximum_security_manager_stack_size(value):
    value is not None and _setenv('Z_MAX_STACK_SIZE', value)
    return value

def publisher_profile_file(value):
    value is not None and _setenv('PROFILE_PUBLISHER', value)
    return value

def http_realm(value):
    value is not None and _setenv('Z_REALM', value)
    return value

def security_policy_implementation(value):
    value not in ('C', None) and _setenv('ZOPE_SECURITY_POLICY', value)

# server handlers

class _RootHandler:
    def __init__(self, options):
        self.options = options

    def __call__(self, config):
        """ Mutate the configuration with defaults and perform
        fixups of values that require knowledge about configuration
        values outside of their context. """

        # set up cgi overrides
        env = {}
        for pair in config.cgi_environment_variables:
            key, value = pair
            self._env[key] = value
        config.cgi_environment_variables = env

        # set up server factories
        factory = ServerFactoryFactory(config)
        l = []

        for section in config.servers:
            # XXX ugly; need to clean this up soon
            server_type = section.getSectionType().replace("-", "_")
            for server_factory in getattr(factory, server_type)(section):
                l.append((server_type, server_factory))

        # if no servers are defined, create default http server and ftp server
        if not l:
            class dummy:
                pass
            http, ftp = dummy(), dummy()

            http.ports = [('', 8080)]
            http.force_connection_close = 0
            ftp.ports = [('', 8021)]

            http = factory.http_server(http)[0]
            ftp = factory.ftp_server(ftp)[0]
            l.extend([('http_server', http), ('ftp_server', ftp)])

        config.servers = l

        # set up defaults for zope_home and client_home if they're
        # not in the config
        if config.zope_home is None:
            config.zope_home   = zope_home(
                os.path.dirname(os.path.dirname(config.software_home))
                )
        if config.client_home is None:
            config.client_home = client_home(
                os.path.join(config.instance_home, 'var')
                )

        # set up defaults for pid_filename and lock_filename if they're
        # not in the config
        if config.pid_filename is None:
            config.pid_filename = os.path.join(config.client_home, 'Z2.pid')
        if config.lock_filename is None:
            config.lock_filename = os.path.join(config.client_home, 'Z2.lock')

        # set up a default root filestorage if there are no root storages
        # mentioned in the config
        databases = config.databases
        root_mounts = [ ('/' in db.mount_points) for db in databases ]
        if not True in root_mounts:
            from datatypes import DBWrapper, Factory
            storagefactory = Factory(
                'ZODB.FileStorage.FileStorage', None,
                os.path.join(config.client_home, 'Data.fs'))
            dbfactory = Factory('ZODB.DB', None)
            databases.append((['/'], DBWrapper(dbfactory, storagefactory)))

        # do command-line overrides
        import cmdline
        opt_processor = cmdline.CommandLineOptions()
        opt_processor(config, self.options)

class ServerFactoryFactory:
    def __init__(self, config):
        self._config = config
        # alias some things for use in server handlers
        from zLOG.AccessLogger import access_logger
        self._logger = access_logger
        import ZODB # :-( required to import user
        from AccessControl.User import emergency_user
        if hasattr(emergency_user, '__null_user__'):
            self._pw = None
        else:
            self._pw = emergency_user._getPassword()
        self._resolver = self.get_dns_resolver()
        self._read_only = config.zserver_read_only_mode
        self._default_ip = config.ip_address
        self._env = config.cgi_environment_variables
        self._module = 'Zope' # no longer settable

    def get_dns_resolver(self):
        if self._config.dns_ip_address:
            from ZServer import resolver
            return resolver.caching_resolver(self._config.dns_ip_address)

    def http_server(self, section):
        l = []
        from ZServer import zhttp_server, zhttp_handler
        for addr, port in section.ports:
            def callback(inst, self=self):
                handler = zhttp_handler(self._module, '', self._env)
                inst.install_handler(handler)
                if section.force_connection_close:
                    handler._force_connection_close = 1
            serverfactory = Factory('ZServer.zhttp_server', callback,
                                    ip=addr, port=port,
                                    resolver=self._resolver,
                                    logger_object=self._logger)
            l.append(serverfactory)
        return l

    def webdav_source_server(self, section):
        l = []
        for addr, port in section.ports:
            def callback(inst, self=self):
                from ZServer.WebDAVSrcHandler import WebDAVSrcHandler
                handler = WebDAVSrcHandler(self._module, '', self._env)
                inst.install_handler(handler)
                if section.force_connection_close:
                    handler._force_connection_close = 1
            serverfactory = Factory('ZServer.zhttp_server', callback,
                                    ip=addr, port=port,
                                    resolver=self._resolver,
                                    logger_object=self._logger)
            l.append(serverfactory)
        return l

    def ftp_server(self, section):
        l = []
        for addr, port in section.ports:
            serverfactory = Factory('ZServer.FTPServer', None,
                                    module=self._module, ip=addr, port=port,
                                    resolver=self._resolver,
                                    logger_object=self._logger)
            l.append(serverfactory)
        return l

    def pcgi_server(self, section):
        if not self._read_only:
            serverfactory = Factory('ZServer.PCGIServer', None,
                                    module=self._module,
                                    ip=self._default_ip,
                                    pcgi_file=section.file,
                                    resolver=self._resolver,
                                    logger_object=self._logger)
            return [serverfactory]
        return []

    def fcgi_server(self, section):
        if section.file and section.port:
            raise ValueError, ("Must specify either 'port' or 'file' in "
                               "fcgi server configuration, but not both")
        if section.port:
            addr = section.port[0]
            port = section.port[1]
        else:
            addr = port = None
        file = section.file
        if not self._read_only:
            serverfactory = Factory('ZServer.FCGIServer', None,
                                    module=self._module, ip=addr, port=port,
                                    socket_file=file, resolver=self._resolver,
                                    logger_object=self._logger)
            return [serverfactory]
        return []

    def monitor_server(self, section):
        if self._pw is None:
            import zLOG
            zLOG.LOG("z2", zLOG.WARNING, 'Monitor server not started'
                     ' because no emergency user exists.')
            return []
        l = []
        for addr, port in section.ports:
            serverfactory = Factory('ZServer.secure_monitor_server', None,
                                    password=self._pw,
                                    hostname=addr,
                                    port=port)
            l.append(serverfactory)
        return l

    def icp_server(self, section):
        l = []
        for addr, port in section.ports:
            serverfactory = Factory('ZServer.ICPServer.ICPServer', None,
                                    addr, port)
            l.append(serverfactory)
        return l

def handleConfig(config, multihandler, options):
    handlers = {}
    for name, value in globals().items():
        if not name.startswith('_'):
            handlers[name] = value
    root_handler = _RootHandler(options)
    handlers['root_handler'] = root_handler
    return multihandler(handlers)
