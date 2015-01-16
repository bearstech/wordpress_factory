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
import os.path


class Project(object):

    def __init__(self):
        with open('wordpress.yml', 'r') as f:
            self.conf = yaml.load(f)

    def docker(self, *args, **opts):
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

    def wp(self, *args):
        args = ['exec', '-ti', 'wordpress-%s' % self.conf['project'], 'wp', '--allow-root'] + list(args)
        return self.docker(*args)

    def mysql(self, *args):
        args = ['exec', '-ti', 'wordpress-%s' % self.conf['project'], 'mysql', '-h', 'db',
                '--password=mypass', '-e'] + list(args)
        return self.docker(*args)


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

project: {project}
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
""".format(project=cwd.split('/')[-1]))
        return

    project = Project()

    if arguments['config']:
        conf = project.conf
        project.mysql("CREATE DATABASE IF NOT EXISTS {name};".format(name=conf['db']['name']))
        project.mysql("CREATE USER '{user}'@'%' IDENTIFIED BY '{password}';".format(user=conf['db']['user'],
                                                                            password=conf['db']['pass']))
        project.mysql("GRANT ALL ON {name}.* TO '{user}'@'%';".format(name=conf['db']['name'],
                                                                     user=conf['db']['user']))
        project.mysql("FLUSH PRIVILEGES;")
        project.wp('core', 'download')
        project.wp('core', 'config', '--skip-check',
           '--dbname=%s' % conf['db']['name'],
           '--dbuser=%s' % conf['db']['user'],
           '--dbpass=%s' % conf['db']['pass'],
           '--dbhost=db'
           )
        project.wp('core', 'install', '--url=%s' % conf['url'],
           '--title="%s"' % conf['name'], '--admin_email=%s' % conf['admin']['email'],
           '--admin_user=%s' % conf['admin']['user'], '--admin_password=%s' %
           conf['admin']['password'])

        for language in conf['language']:
            if language != 'en':
                project.wp('core', 'language', 'install', language)
                project.wp('core', 'language', 'activate', language)

        if 'plugin' in conf:
            for plugin in conf['plugin']:
                project.wp('plugin', 'install', plugin)
                project.wp('plugin', 'activate', plugin)

        domain = conf['url'].split(':')[0]
        p = project.conf['project']
        project.docker('exec', '-ti', 'wordpress-%s' % p, '/opt/website_conf.py', domain)
        project.docker('exec', '-ti', 'wordpress-%s' % p, 'kill', '-HUP', '1')

    if arguments['build']:

        here = os.path.dirname(__file__)
        if arguments['wordpress']:
            project.docker('build', '-t', 'wordpress',
                           os.path.join(here, 'docker', 'wordpress'))
        if arguments['mysql']:
            project.docker('build', '-t', 'mysql', os.path.join(here, 'docker', 'mysql'))

    if arguments['run']:
        p = project.conf['project']
        if arguments['wordpress']:
            if not os.path.exists('log'):
                os.mkdir('log')
                if not os.path.exists('log/test.example.com'):
                    os.mkdir('log/test.example.com')
            if not os.path.exists('dump'):
                os.mkdir('dump')
            project.docker('run', '--name=wordpress-%s' % p,
                           '-d', '-p', '8000:80',
                           '--hostname=wordpress.example.com',
                           '--volume' , '%s/wordpress:/var/www/test/root' % cwd,
                           '--volume', '%s/log:/var/log/apache2/' % cwd,
                           '--volume', '%s/dump:/dump/' % cwd,
                           '--link=mysql-%s:db' % p, 'wordpress')
        elif arguments['mysql']:
            project.docker('run', '--name=mysql-%s' % p, '-d',
                           '-p', '3306', 'mysql')
        else:
            # [FIXME] build both
            pass

    if arguments['update']:
        project.wp('cron', 'event', 'run', 'wp_version_check')
        project.wp('cron', 'event', 'run', 'wp_update_themes')
        project.wp('cron', 'event', 'run', 'wp_update_plugins')
        project.wp('cron', 'event', 'run', 'wp_maybe_auto_update')
        project.wp('plugin', 'list', '--fields=name,version,update_version')
        project.wp('theme', 'list', '--fields=name,version,update_version')
        project.wp('core', 'check-update')

    if arguments['upgrade']:
        project.wp('plugin', 'update', '--all')
        project.wp('theme', 'update', '--all')
        project.wp('core', 'verify-checksums')
        project.wp('core', 'update')
        project.wp('core', 'update-db')

    if arguments['db']:
        if arguments['export']:
            project.wp('db', 'export', '/dump/dump.sql')

    if arguments['wxr']:
        if arguments['export']:
            project.wp('export', '--dir=/dump/')

if __name__ == '__main__':
    main()
