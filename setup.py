#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='wpfactory',
    version='0.1',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={
        'wpfactory': ['docker/wordpress/*', 'docker/mysql/*'],
    },
    entry_points={
        'console_scripts': ['wpfactory=wpfactory:main']
    }
)
