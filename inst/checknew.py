import sys


def main():
    import pkg_resources
    from pkg_resources import parse_requirements
    from setuptools.package_index import PackageIndex

    ws = pkg_resources.require('Zope2')
    pi = PackageIndex()

    names = []
    installed = []
    for dist in ws:
        name = dist.project_name
        if name not in names:
            names.append(name)
            installed.append(dict(
                dist=dist,
                name=name,
                req=parse_requirements(name).next(),
                ))

    def _key(value):
        return value['name']
    installed.sort(key=_key)

    upgrade = False
    for info in installed:
        print("Checking for new version of %s." % info['name'])
        new_dist = pi.obtain(info['req'])
        if new_dist.parsed_version > info['dist'].parsed_version:
            upgrade = True
            print()
            print("Newer version for %s found. Installed: %s - found: %s" %
                (info['name'], info['dist'].version, new_dist.version))
            print("Newer version available at: %s" % new_dist.location)
            print()

    if not upgrade:
        print("No updates have been found. All packages use current versions.")


def help():
    print("Use this script via ./bin/zopepy inst/checknew.py.")


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--help' in args:
        help()
    else:
        main()
