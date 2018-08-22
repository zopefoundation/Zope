from setuptools import setup, find_packages
import os


version = '1.0.dev0'


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()


long_description = (
    read('README.rst')
    + '\n' +
    read('CHANGES.rst'))


setup(
    name='zmi.styles',
    version=version,
    description="ZMI styling for Zope 4.",
    long_description=long_description,
    classifiers=[],
    keywords='',
    license='ZPL 2.1',
    author='Zope Foundation and Contributors',
    author_email='zope-dev@zope.org',
    packages=find_packages(),
    namespace_packages=['zmi'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Zope',
        'setuptools',
        'zope.component',
        'zope.interface',
    ],
)
