#!/usr/bin/env python
# encoding:utf8

"""
Wordpress factory.

Usage:
    wpfactory scaffold
    wpfactory run mysql
    wpfactory run wordpress
    wpfactory config
    wpfactory build mysql
    wpfactory build wordpress
    wpfactory update
    wpfactory upgrade
    wpfactory db export
    wpfactory wxr export

Options:
    --json                         Json output
"""

__version__ = '0.1'

from subprocess import Popen, PIPE
import os
import sys
import yaml
from cStringIO import StringIO
from docopt import docopt
import os
import os.path

here = os.path.dirname(__file__)


def docker(*args, **opts):
    print "$ ", " ".join(['docker'] + list(args))
    p = Popen(['docker'] + list(args), stdout=PIPE, stderr=PIPE, **opts)
    f = StringIO()
    for line in iter(p.stdout.readline, ''):
        sys.stdout.write(line)
        f.write(line)
    e = p.stderr.read()
    if e:
        raise Exception(e)
    return f


def wp(*args):
    args = ['exec', '-ti', 'wordpress', 'wp', '--allow-root'] + list(args)
    return docker(*args)


def mysql(*args):
    args = ['exec', '-ti', 'wordpress', 'mysql', '-h', 'db',
            '--password=mypass', '-e'] + list(args)
    return docker(*args)


def config():
    with open('wordpress.yml', 'r') as f:
        conf = yaml.load(f)
    return conf


def main():

    arguments = docopt(__doc__, version='Wordpress Manager %s' % __version__)

    cwd = os.getcwd()

    if arguments['scaffold']:
        if not os.path.exists('wordpress'):
            os.makedirs('wordpress')
        if not os.path.exists('wordpress.yml'):
            with open('wordpress.yml', 'w') as f:
                f.write("""---

# Scaffolded Wordpress Factory config file.


url: test.example.lan:8000
name: Wordpress Factory Test
language:
    - en
admin:
    email: admin@example.lan
    user: admin
    password: password
db:
    name: test
    user: test
    pass: password
""")

    if arguments['config']:
        conf = config()
        mysql("CREATE DATABASE IF NOT EXISTS {name};".format(name=conf['db']['name']))
        mysql("CREATE USER '{user}'@'%' IDENTIFIED BY '{password}';".format(user=conf['db']['user'],
                                                                            password=conf['db']['pass']))
        mysql("GRANT ALL ON {name}.* TO '{user}'@'%';".format(name=conf['db']['name'],
                                                                     user=conf['db']['user']))
        mysql("FLUSH PRIVILEGES;")
        wp('core', 'download')
        wp('core', 'config', '--skip-check',
           '--dbname=%s' % conf['db']['name'],
           '--dbuser=%s' % conf['db']['user'],
           '--dbpass=%s' % conf['db']['pass'],
           '--dbhost=db'
           )
        wp('core', 'install', '--url=%s' % conf['url'],
           '--title="%s"' % conf['name'], '--admin_email=%s' % conf['admin']['email'],
           '--admin_user=%s' % conf['admin']['user'], '--admin_password=%s' %
           conf['admin']['password'])

        for language in conf['language']:
            if language != 'en':
                wp('core', 'language', 'install', language)
                wp('core', 'language', 'activate', language)

        for plugin in conf['plugin']:
            wp('plugin', 'install', plugin)
            wp('plugin', 'activate', plugin)

        domain = conf['url'].split(':')[0]
        docker('exec', '-ti', 'wordpress', '/opt/website_conf.py', domain)
        docker('exec', '-ti', 'wordpress', 'kill', '-HUP', '1')

    if arguments['build']:

        here = os.path.dirname(__file__)
        if arguments['wordpress']:
            docker('build', '-t', 'wordpress', os.path.join(here, 'docker', 'wordpress'))
        if arguments['mysql']:
            docker('build', '-t', 'mysql', os.path.join(here, 'docker', 'mysql'))

    if arguments['run']:
        if arguments['wordpress']:
            if not os.path.exists('log'):
                os.mkdir('log')
            if not os.path.exists('dump'):
                os.mkdir('dump')
            docker('run',  '--name=wordpress', '--hostname=wordpress.example.com', '-d', '-p', '8000:80',
                   '--volume' , '%s/wordpress:/var/www/test/root' % cwd,
                   '--volume', '%s/log:/var/log/apache2/' % cwd,
                   '--volume', '%s/dump:/dump/' % cwd,
                         '--link=mysql:db', 'wordpress')
        elif arguments['mysql']:
            docker('run', '--name=mysql', '-d', '-p', '3306', 'mysql')
        else:
            pass

    if arguments['update']:
        wp('cron', 'event', 'run', 'wp_version_check')
        wp('cron', 'event', 'run', 'wp_update_themes')
        wp('cron', 'event', 'run', 'wp_update_plugins')
        wp('cron', 'event', 'run', 'wp_maybe_auto_update')
        wp('plugin', 'list', '--fields=name,version,update_version')
        wp('theme', 'list', '--fields=name,version,update_version')
        wp('core', 'check-update')

    if arguments['upgrade']:
        wp('plugin', 'update', '--all')
        wp('theme', 'update', '--all')
        wp('core', 'verify-checksums')
        wp('core', 'update')
        wp('core', 'update-db')

    if arguments['db']:
        if arguments['export']:
            wp('db', 'export', '/dump/dump.sql')

    if arguments['wxr']:
        if arguments['export']:
            wp('export', '--dir=/dump/')

if __name__ == '__main__':
    main()
