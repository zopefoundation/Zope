import optparse
import os
import os.path
import sys
import re

here = os.path.abspath(os.path.dirname(__file__))

# I would use string.Template, but it's just too hard to change it to
# respect only ${brace} syntax instead of both that and $name syntax.
TOKEN_RE = re.compile(r'\$\{([\.\w/-]+)\}')
def rewrite(repltext, **kw):
    def replace(match):
        return kw[match.group(1)]
    return TOKEN_RE.sub(replace, repltext)

def mkinstance(conf):
    sandbox = conf['sandbox']
        
    for dir in ('bin', 'etc', 'var', 'Products', 'import', 'log'):
        path = os.path.join(sandbox, dir)
        if not os.path.exists(path):
            os.makedirs(path)

    try:
        # this is (stupidly) required by the zdrun key in the <runner>
        # section of zeo.conf
        import zdaemon
        conf['zdaemon_pkgdir'] = zdaemon.__path__[0]
    except ImportError:
        conf['zdaemon_pkgdir'] = '{unknown}'

    zope_conf = conf['zope_conf']
    site_zcml = conf['site_zcml']
        
    for source, target in (
        ('zope2.ini', 'zope2.ini'),
        (site_zcml, 'site.zcml'),
        (zope_conf, 'zope.conf'),
        ('apache2.conf', 'apache2.conf'),
        ('zeo.conf', 'zeo.conf'),
        ):
        template = open(os.path.join(here, 'etc', source), 'r').read()
        result = rewrite(template, **conf)
        targetfile = os.path.join(sandbox, 'etc', target)
        if not os.path.exists(targetfile):
            open(targetfile, 'w').write(result)

    template = open(os.path.join(here, 'etc', 'zope2.wsgi'), 'r').read()
    result = rewrite(template, **conf)
    targetfile = os.path.join(sandbox, 'bin', 'zope2.wsgi')
    if not os.path.exists(targetfile):
        open(targetfile, 'w').write(result)
        os.chmod(targetfile, 0755)

def main(argv=sys.argv):
    """ Console script target """
    parser = optparse.OptionParser(
        usage='%prog [OPTIONS]'
        )
    parser.add_option('-s', '--sandbox', action='store', dest='sandbox',
                      default='.', help='Create the instance in this directory')
    parser.add_option('-p', '--zope-port', action='store', dest='zope_port',
                      default='8080', help='Zope HTTP port')
    parser.add_option('-j', '--zeo-port', action='store', dest='zeo_port',
                      default='8100', help='ZEO server port number')
    parser.add_option('-z', '--use-zeo', action='store_true', dest='use_zeo',
                      default=False, help='Use ZEO to house main storage')
    options, args = parser.parse_args(argv)
    try:
        # Zope 2.10+ (Five 1.5.3?+)
        from Products.Five.fivedirectives import IRegisterPackageDirective
        options.site_zcml = 'zope-2.10+-site.zcml'
    except ImportError:
        # Zope 2.9 (or Five before 1.5.3?)
        options.site_zcml = 'zope-2.9-site.zcml'
    if options.use_zeo:
        options.zope_conf = 'zope-zeoclient.conf'
    else:
        options.zope_conf = 'zope-nonzeoclient.conf'
    options.python = sys.executable
    conf = options.__dict__
    sandbox = conf['sandbox']
    conf['sandbox'] = os.path.abspath(os.path.normpath(os.path.expanduser(
        sandbox)))
    mkinstance(conf)
