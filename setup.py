from setuptools import setup
import sys

import libcli

if sys.version_info.major < 3:
    raise Exception('Python 3 required')

setup(
    name='libcli',
    version=libcli.__version__,
    description='Library helps to build command line interface',
    long_description=open('README.rst').read(),

    license='MIT',
    url='https://github.com/stepheny/pylibcli',
    author='Stephen.Y',
    author_email='stephen.jin.yee@gmail.com',

    packages=['libcli'],
    test_suite = 'tests',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    )
