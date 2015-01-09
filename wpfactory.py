#!/usr/bin/env python
# encoding:utf8

"""
Wordpress factory.

Usage:
    wpfactory scaffold
    wpfactory start mysql
    wpfactory start wordpress
    wpfactory build mysql
    wpfactory build wordpress

Options:
    --json                         Json output
"""

__version__ = '0.1'

from subprocess import Popen, PIPE


def docker(*args):
    p = Popen(['docker'] + list(args), stdout=PIPE, stderr=PIPE)
    p.wait()
    e = p.stderr.read()
    if e:
        raise e
    return p.stdout.read()


if __name__ == '__main__':
    from docopt import docopt

    arguments = docopt(__doc__, version='Wordpress Manager %s' % __version__)
    print arguments

    if arguments['build']:
        if arguments['wordpress']:
            print docker('build', '-t', 'wordpress', './docker/wordpress')
        if arguments['mysql']:
            print docker('build', '-t', 'wordpress', './docker/wordpress')


