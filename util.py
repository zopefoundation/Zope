import os
from configparser import RawConfigParser


HERE = os.path.abspath(os.path.dirname(__file__))


class CaseSensitiveParser(RawConfigParser):

    def optionxform(self, value):
        return value


def generate(in_, requirements_file, constraints_file):
    in_file = os.path.join(HERE, in_)
    out_file_requirements = os.path.join(HERE, requirements_file)
    out_file_constraints = os.path.join(HERE, constraints_file)
    parser = CaseSensitiveParser()
    parser.read(in_file)

    requirements = []
    constraints = []
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

        spec = f'{name}=={pin}'
        requirements.append(spec + '\n')
        constraints.append(spec + '\n')

    with open(out_file_requirements, 'w') as fd:
        fd.write(zope_requirement)
        for req in sorted(requirements):
            fd.write(req)
    with open(out_file_constraints, 'w') as fcon:
        for con in sorted(constraints):
            fcon.write(con)


def main():
    generate('versions-prod.cfg', 'requirements-full.txt', 'constraints.txt')


if __name__ == '__main__':
    main()
