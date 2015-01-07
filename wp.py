#!/usr/bin/env python
# encoding:utf8

import requests
import requests_cache

requests_cache.install_cache('wp_cache', backend='sqlite', expire_after=300)


class Wordpress(object):

    def __init__(self):
        self.session = requests.Session()

    def version(self):
        r = requests.get('https://api.wordpress.org/core/version-check/1.7/')
        return r.json()

    def plugin(self, slug):
        r = requests.get('https://api.wordpress.org/plugins/info/1.0/{slug}.json'.format(slug=slug))
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
    from pprint import pprint
    import json
    import sys
    w = Wordpress()
    #pprint(w.plugin('secure-wordpress'))
    old = json.load(open(sys.argv[1]))
    for new, name, versions in w.plugin_outdated(old, ['bnp']):
        print "✓" if new else "☠", name, "%s => %s" % versions if new else ""

