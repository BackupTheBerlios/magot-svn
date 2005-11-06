# -*- coding: UTF-8 -*-

from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

setup(
    name = "Magot",
    version = "0.1",

    # scripts = ['bin/magot'],
    
    packages = find_packages('src/py', exclude=['*.sandbox']),
    package_dir = {'':'src/py'},
    package_data = {'magot': ['*.list', '*.ini']},

    # install_requires = ['PEAK>=0.5a3'],

    # metadata for upload to PyPI
    description = "Cross-platform personal finance manager.",
    author = "Jean-Philippe Dutrève",
    author_email = "jdutreve@users.berlios.de",
    url = "http://developer.berlios.de/projects/magot/",
    license = "LGPL",
    platforms = ['UNIX', 'Windows'],    
    keywords = ['accounting', 'finance', 'python', 'wxpython', 'PEAK'],
    
    zip_safe = False
)
