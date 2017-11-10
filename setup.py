#!/usr/bin/env python3

from setuptools import setup, find_packages
import rundoc

setup(
    name = 'rundoc',
    description = rundoc.__doc__.strip(),
    url = 'https://github.com/EclecticIQ/rundoc',
    download_url = 'https://github.com/EclecticIQ/rundoc/archive/'+rundoc.__version__+'.tar.gz',
    version = rundoc.__version__,
    author = rundoc.__author__,
    author_email = rundoc.__author_email__,
    license = rundoc.__licence__,
    packages = [ 'rundoc' ],
    entry_points={ 
        'console_scripts': [
            'rundoc=rundoc.__main__:main',
        ],
    },
    install_requires = [
        'markdown>=2.6.9',
        'argcomplete>=1.9.2',
        'bs4',
    ],
    python_requires=">=3.4.7",
)

