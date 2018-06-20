#!/usr/bin/env python3

from setuptools import setup, find_packages
import os
import rundoc

def here(*path):
    return os.path.join(os.path.dirname(__file__), *path)

def get_file_contents(filename):
    with open(here(filename), 'r', encoding='utf8') as fp:
        return fp.read()

setup(
    name = 'rundoc',
    description = rundoc.__doc__.strip(),
    long_description=get_file_contents('README.md'),
    url = 'https://gitlab.com/nul.one/rundoc',
    download_url = 'https://gitlab.com/nul.one/rundoc/-/archive/{0}/rundoc-{0}.tar.gz'.format(rundoc.__version__),
    version = rundoc.__version__,
    author = rundoc.__author__,
    author_email = rundoc.__author_email__,
    license = rundoc.__license__,
    packages = [ 'rundoc' ],
    entry_points={ 
        'console_scripts': [
            'rundoc=rundoc.__main__:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Customer Service',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Documentation',
        'Topic :: Software Development :: Documentation',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',
    ],
    install_requires = [
        'argcomplete>=1.9.2,<2.0',
        'beautifulsoup4>=4.4.1,<5.0',
        'markdown>=2.6.9,<3.0',
        'prompt_toolkit>=2.0,<3.0',
        'pygments>=2.2.0,<3.0',
    ],
    python_requires=">=3.4.6",
)

