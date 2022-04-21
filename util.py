import os
from typing import Optional, Tuple, List
from configparser import RawConfigParser


HERE = os.path.abspath(os.path.dirname(__file__))
PYTHON_VERSIONED = {}


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
    zope_requirement = (
        '-e git+https://github.com/zopefoundation/Zope.git@master#egg=Zope\n')
    zope_requirement = _generate(
        parser.items('versions:python36'), '3.6', requirements, constraints,
        zope_requirement)
    zope_requirement = _generate(
        parser.items('versions:python35'), '3.5', requirements, constraints,
        zope_requirement)
    zope_requirement = _generate(
        parser.items('versions:python27'), '2.7', requirements, constraints,
        zope_requirement)
    # "Unversioned" pins must come last, how they are handled depends on
    # Python version qualifiers for dependencies of the same name.
    zope_requirement = _generate(
        parser.items('versions'), None, requirements, constraints,
        zope_requirement)

    with open(out_file_requirements, 'w') as fd:
        fd.write(zope_requirement)
        for req in sorted(requirements):
            fd.write(req)
    with open(out_file_constraints, 'w') as fcon:
        for con in sorted(constraints):
            fcon.write(con)


def _generate(
    versions: List[Tuple[str, str]],
    python_version: Optional[str],
    requirements: List[str],
    constraints: List[str],
    zope_requirement: str
) -> str:
    """Generate requirements and constraints for a specific Python version.

    If ``python_version`` is falsy, generate for all python versions.
    Returns a probably changed ``zope_requirement``.
    """
    global PYTHON_VERSIONED

    for name, pin in versions:
        if name == 'Zope':
            if pin:
                zope_requirement = 'Zope==%s\n' % pin
            continue

        if not pin:
            continue

        spec = f'{name}=={pin}'
        if python_version:
            spec = f"{spec}; python_version == '{python_version}'"

            versions = PYTHON_VERSIONED.get(name, set())
            versions.add(python_version)
            PYTHON_VERSIONED[name] = versions
        else:
            if name in PYTHON_VERSIONED:
                versions = sorted(PYTHON_VERSIONED.get(name))
                spec = f"{spec}; python_version > '{versions[-1]}'"

        requirements.append(spec + '\n')
        constraints.append(spec + '\n')
    return zope_requirement


def main():
    generate('versions-prod.cfg', 'requirements-full.txt', 'constraints.txt')


if __name__ == '__main__':
    main()
