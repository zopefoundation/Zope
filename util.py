from ConfigParser import RawConfigParser
import os

HERE = os.path.abspath(os.path.dirname(__file__))


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
        '-e git+https://github.com/zopefoundation/Zope.git@master#egg=Zope2\n')
    for name, pin in versions:
        if name == 'Zope2':
            if pin:
                zope_requirement = 'Zope2==%s\n' % pin
            continue

        if not pin:
            continue
        requirements.append('%s==%s\n' % (name, pin))

    with open(out_file, 'wb') as fd:
        fd.write(zope_requirement)
        for req in sorted(requirements):
            fd.write(req)


def main():
    generate('versions-prod.cfg', 'requirements.txt')


if __name__ == '__main__':
    main()
