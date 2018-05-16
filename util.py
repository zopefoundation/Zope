import os

try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser

HERE = os.path.abspath(os.path.dirname(__file__))

PY2_ONLY = [
    'ZServer',
]


class CaseSensitiveParser(RawConfigParser):

    def optionxform(self, value):
        return value


def generate(in_, out):
    in_file = os.path.join(HERE, in_)
    out_file = os.path.join(HERE, out)

    parser = CaseSensitiveParser()
    parser.read(in_file)

    requirements = []
    versions = parser.items('versions')
    zope_requirement = (
        '-e git+https://github.com/zopefoundation/Zope.git@master#egg=Zope\n')
    for name, pin in versions:
        if name == 'Zope':
            if pin:
                zope_requirement = 'Zope==%s\n' % pin
            continue

        if not pin:
            continue

        spec = '%s==%s' % (name, pin)
        if name in PY2_ONLY:
            spec += " ; python_version < '3.0'"
        requirements.append(spec + '\n')

    with open(out_file, 'w') as fd:
        fd.write(zope_requirement)
        for req in sorted(requirements):
            fd.write(req)


def main():
    generate('versions-prod.cfg', 'requirements-full.txt')


if __name__ == '__main__':
    main()
