# Stock __traceback_supplement__ implementations

class PathTracebackSupplement:
    """Implementation of ITracebackSupplement"""
    pp = None
    def __init__(self, object):
        self.object = object
        if hasattr(object, 'getPhysicalPath'):
            self.pp = '/'.join(object.getPhysicalPath())
        if hasattr(object, 'absolute_url'):
            self.source_url = '%s/manage_main' % object.absolute_url()

    def getInfo(self, as_html=0):
        if self.pp is None:
            return
        if as_html:
            from cgi import escape
            return '<b>Physical Path:</b>%s' % (escape(self.pp))
        else:
            return '   - Physical Path: %s' % self.pp
