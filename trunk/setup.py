#!/usr/bin/python2.4
# -*- coding: UTF-8 -*-
"""Distutils setup file"""

from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

setup(
    name = "Magot",
    version = "0.1",

    description = "A cross-platform personal finance manager.",
    author = "Jean-Philippe Dutrève",
    author_email = "jdutreve@users.berlios.de",
    url = "http://developer.berlios.de/projects/magot/",
	download_url="http://developer.berlios.de/projects/magot/",
    license = "LGPL",
    platforms = ['UNIX', 'Windows'],

	scripts = ['bin/magot'],

    package_dir = {'':'src/py'},
    packages = find_packages('src/py', exclude=['*.sandbox']),
    package_data = {'magot': ['*.ini']},

    install_requires = ['PEAK>=0.5a3'],

	entry_points = {
        "console_scripts":["magot = magot.commands:runMain"]
    },
	zip_safe = False,
	
    long_description = """\
A cross-platform personal finance manager written in a agile way with Python.
""",
    
	keywords = "accounting,finance,Python,WxPython,PEAK,component,framework",
)
