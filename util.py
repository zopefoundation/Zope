import os
from configparser import NoSectionError
from configparser import RawConfigParser
from typing import Optional


HERE = os.path.abspath(os.path.dirname(__file__))
PYTHON_VERSIONED = {}


class CaseSensitiveParser(RawConfigParser):

    def optionxform(self, value):
        return value


def generate(
        buildout_file: str,
        requirements_file: str,
        zope_requirement: str):
    out_file_requirements = os.path.join(HERE, requirements_file)
    parser = CaseSensitiveParser()
    parser.read(os.path.join(HERE, buildout_file))
    for extend in parser.get('buildout', 'extends', fallback='').splitlines():
        extend = extend.strip()
        if extend:
            parser.read(os.path.join(HERE, extend))

    requirements = []

    # Try to include sections for all currently supported Python versions
    for py_version in ('3.9', '3.10', '3.11', '3.12', '3.13'):
        short_version = py_version.replace('.', '')
        try:
            zope_requirement = _generate(
                parser.items(f'versions:python{short_version}'), py_version,
                requirements, zope_requirement)
        except NoSectionError:
            continue

    # "Unversioned" pins must come last, how they are handled depends on
    # Python version qualifiers for dependencies of the same name.
    zope_requirement = _generate(
        parser.items('versions'), None, requirements, zope_requirement)

    with open(out_file_requirements, 'w') as fd:
        fd.write(zope_requirement)
        for req in sorted(requirements):
            fd.write(req)


def _generate(
    versions: list[tuple[str, str]],
    python_version: Optional[str],
    requirements: list[str],
    zope_requirement: str
) -> str:
    """Generate requirements or constraints file for a specific Python version.

    If ``python_version`` is false, generate for all python versions.
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
                versions = sorted(PYTHON_VERSIONED.get(name),
                                  key=lambda s: list(map(int, s.split('.'))))
                spec = f"{spec}; python_version > '{versions[-1]}'"

        requirements.append(spec + '\n')
    return zope_requirement


def main():
    generate(
        'versions-prod.cfg',
        'requirements-full.txt',
        '-e git+https://github.com/zopefoundation/Zope.git@master#egg=Zope\n',
    )
    generate('versions.cfg', 'constraints.txt', '')


if __name__ == '__main__':
    main()
