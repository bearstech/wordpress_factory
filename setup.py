#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='wpfactory',
    description='A factory to prepare, deploy, upgrade your Wordpress.'+
    " Also Docker.",
    version='0.3',
    author='Mathieu Lecarme',
    author_email='mlecarme@bearstech.com',
    maintainer='Johan Charpentier',
    maintainer_email='jcharpentier@bearstech.com',
    url='https://github.com/bearstech/wordpress_factory',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={
        'wpfactory': ['docker/wordpress/*', 'docker/mysql/*',
                      'docker/sitespeed/*', 'docker/mailhog/*'],
    },
    entry_points={
        'console_scripts': ['wpfactory=wpfactory:main']
    },
    install_requires=[
        'pyyaml',
        'clint',
        'requests>=2.20.0',
        'backports.ssl-match-hostname',
        'docker-compose'
    ]
)
