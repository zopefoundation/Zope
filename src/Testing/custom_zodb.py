import logging
import os


LOG = logging.getLogger('Testing')


def getStorage():
    """ Return a storage instance for running ZopeTestCase based
        tests. By default a DemoStorage is used. Setting
        $TEST_ZEO_HOST/TEST_ZEO_PORT environment variables allows you
        to use a ZEO server instead. A file storage can be configured
        by settting the $TEST_FILESTORAGE environment variable.
    """

    get = os.environ.get

    if 'TEST_ZEO_HOST' in os.environ and 'TEST_ZEO_PORT' in os.environ:
        from ZEO.ClientStorage import ClientStorage
        zeo_host = get('TEST_ZEO_HOST')
        zeo_port = int(get('TEST_ZEO_PORT'))
        LOG.info('Using ZEO server (%s:%d)' % (zeo_host, zeo_port))
        return ClientStorage((zeo_host, zeo_port))

    elif 'TEST_FILESTORAGE' in os.environ:
        import ZODB.FileStorage
        datafs = get('TEST_FILESTORAGE')
        LOG.info('Using Filestorage at (%s)' % datafs)
        return ZODB.FileStorage.FileStorage(datafs)

    else:
        from ZODB.DemoStorage import DemoStorage
        LOG.info('Using DemoStorage')
        return DemoStorage()


Storage = getStorage()
