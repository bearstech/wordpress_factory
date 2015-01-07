#!/usr/bin/env python
# encoding:utf8

"""
Wordpress manager.

Usage:
    wp.py plugin --path=<path> --server=<server> [--user=<user>] [--json]

Options:
    --json                         Json output
    -s <server>, --server=<server> Server
    -p <path>, --path=<path>       Worpdress root path
    -u <user>, --user=<user>       SSH user [default: root]
"""

__version__ = '0.1'
import requests
import requests_cache

requests_cache.install_cache('wp_cache', backend='sqlite', expire_after=300)


class Wordpress(object):

    def __init__(self):
        self.session = requests.Session()

    def version(self):
        r = self.session.get('https://api.wordpress.org/core/version-check/1.7/', verify=True)
        return r.json()

    def plugin(self, slug):
        r = self.session.get('https://api.wordpress.org/plugins/info/1.0/{slug}.json'.format(slug=slug), verify=True)
        if r.status_code != 200:
            return None
        return r.json()

    def plugin_outdated(self, plugins, prefix=[]):
        for plugin in plugins:
            if plugin['version'] == '':
                continue
            if plugin['name'].split('-')[0] in prefix:
                continue
            n = self.plugin(plugin['name'])
            if n is None:
                yield False, plugin['name'], None
                continue
            requires = n['requires']
            version = n['version']
            if version != plugin['version']:
                yield True, plugin['name'], (plugin['version'], version)


if __name__ == '__main__':
    from docopt import docopt
    import json
    import sys
    import subprocess

    arguments = docopt(__doc__, version='Wordpress Manager %s' % __version__)

    w = Wordpress()

    if arguments['plugin']:
        server = arguments['--server']
        path = arguments['--path']
        user = arguments['--user']
        js = arguments.get('--json', False)
        cmd = subprocess.Popen(['ssh', '%s@%s' % (user, server),
                                '/root/wp-cli.phar', '--allow-root',
                                '--path=%s' % path, 'plugin', 'list',
                                '--fields=name,status,version,update_version',
                                '--format=json'], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        old = cmd.stdout.readlines()[-1]
        old = json.loads(old)
        out = sys.stdout
        if js:
            out.write("[")
        for new, name, versions in w.plugin_outdated(old, ['bnp']):
            if js:
                json.dump(dict(new=new, name=name, versions=versions), out)
            else:
                out.write("✓ " if new else "☠ ")
                out.write(name)
                out.write(" %s => %s" % versions if new else "")
                out.write("\n")
        if js:
            out.write("]")
