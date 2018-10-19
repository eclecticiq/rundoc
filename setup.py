#!/usr/bin/env python3

import rundoc as project

from setuptools import setup, find_packages
import os

def here(*path):
    return os.path.join(os.path.dirname(__file__), *path)

def get_file_contents(filename):
    with open(here(filename), 'r', encoding='utf8') as fp:
        return fp.read()

setup(
    name = project.__name__,
    description = project.__doc__.strip(),
    long_description=get_file_contents('README.md'),
    url = 'https://gitlab.com/nul.one/' + project.__name__,
    download_url = 'https://gitlab.com/nul.one/{1}/-/archive/{0}/{1}-{0}.tar.gz'.format(project.__version__, project.__name__),
    version = project.__version__,
    author = project.__author__,
    author_email = project.__author_email__,
    license = project.__license__,
    packages = [ project.__name__ ],
    entry_points={ 
        'console_scripts': [
            '{0}={0}.__main__:cli'.format(project.__name__),
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
        'beautifulsoup4>=4.4.1,<5.0',
        'click>=6.7,<8.0',
        'markdown>=2.6.9,<3.0',
        'markdown-rundoc>=0.2.1,<0.3.0',
        'prompt_toolkit>=2.0,<3.0',
        'pygments>=2.2.0,<3.0',
    ],
    python_requires=">=3.4.6",
)

