#!/usr/bin/env python
# encoding:utf8

"""
Wordpress factory.

Usage:
    wpfactory scaffold
    wpfactory build [mysql|wordpress|sitespeed] [--no-cache]
    wpfactory run [mysql|wordpress]
    wpfactory start
    wpfactory stop
    wpfactory config
    wpfactory update
    wpfactory upgrade
    wpfactory db export [--contents|--no-contents|--options]
    wpfactory wxr export
    wpfactory dictator export
    wpfactory home
    wpfactory sitespeed
    wpfactory

Options:
    -h --help   Show this screen.
    --json      Json output
    --no-wxr    Export all except WXR stuff
"""

__version__ = '0.1'

from subprocess import Popen, PIPE
from clint.textui import colored, puts
import os
import sys
import yaml
from cStringIO import StringIO
from docopt import docopt
import os.path
import webbrowser
import re
import platform

DOCKER_ERROR = re.compile(r'time="(.*?)" level="(.*?)" msg="(.*?)"')
SPACES = re.compile(r'\s\s+')


SCAFFOLD_TEMPLATE = """---

# Scaffolded Wordpress Factory config file.

project: {project}
url: {docker_host}:8000
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
"""

def error(msg, source=''):
    print "\n[Error {source}] {msg}".format(source=source, msg=msg)
    sys.exit(1)


class DockerException(Exception):
    pass


class DockerNotRunningException(DockerException):
    pass

class DockerCommandException(DockerException):
    "Docker is fine, but the command not"
    pass

class Project(object):

    def __init__(self):
        if not os.path.exists('wordpress.yml'):
            print __doc__
            error("Can't find wordpress.yml file, use:\n$ wpfactory scaffold\nand edit it." )
        with open('wordpress.yml', 'r') as f:
            self.conf = yaml.load(f)

    def docker(self, *args, **opts):
        cmdline = "$ " + " ".join(['docker'] + list(args))
        puts(colored.yellow(cmdline))
        p = Popen(['docker'] + list(args), stdout=PIPE, stderr=PIPE, **opts)
        f = StringIO()
        for line in iter(p.stdout.readline, ''):
            sys.stdout.write(line)
            f.write(line)
        p.wait()
        error = p.returncode != 0
        if error:
            e = p.stderr.read()
            if e.find('level="fatal" msg="An error occurred trying to connect:') != -1:
                raise DockerNotRunningException(e)
            m = DOCKER_ERROR.match(e)
            if m:
                raise DockerException(m.group(3), m.group(2))
            f.seek(0)
            raise DockerCommandException(e, f.read())
        f.seek(0)
        return f

    def wp(self, *args):
        args = ['exec', '-ti', 'wordpress-%s' % self.conf['project'],
                'wp', '--allow-root', '--path=/var/www/test/root',
                '--require=/opt/dictator/dictator.php'] + list(args)
        return self.docker(*args)

    def mysql(self, *args):
        args = ['exec', '-ti', 'wordpress-%s' % self.conf['project'], 'mysql', '-h', 'db',
                '--password=mypass', '-e'] + list(args)
        return self.docker(*args)

    def services(self):
        "Started services."
        s = set()
        project = self.conf['project']
        for service in [SPACES.split(ps)[:-1][-1] for ps in
                        self.docker('ps').readlines()[1:]]:
            if service.split('-')[-1] == project:
                s.add(service[:-(len(project)+1)])
        return s

def guess_docker_host():
        d = os.environ.get('DOCKER_HOST', None)
        if d:
            return d.split('//')[-1].split(':')[0]
        else:
            return "localhost"


def main():

    arguments = docopt(__doc__, version='Wordpress Manager %s' % __version__)

    cwd = os.getcwd()

    if arguments['scaffold']:
        # [FIXME] boot2docker can share folder on /tmp/ path

        if not os.path.exists('wordpress'):
            os.makedirs('wordpress')
        if os.path.exists('wordpress.yml'):
            error("wordpress.yml already exist.")
        else:
            with open('wordpress.yml', 'w') as f:
                f.write(SCAFFOLD_TEMPLATE.format(project=cwd.split('/')[-1],
                                                 docker_host=guess_docker_host()))
                print "Just scaffolded the wordpress.yml file, edit it."
        return

    else:
        project = Project()

    if arguments['config']:
        conf = project.conf
        r = project.docker('exec', '-ti', 'wordpress-%s' % conf['project'],
                       'mysql', '-h', 'db', '-u', conf['db']['user'],
                       '--password=%s' % conf['db']['pass'],
                       conf['db']['name'], '-e', 'SELECT 1+1;'
                       )
        result = r.read()
        print "result : %s" % result
        if "ERROR" in result:
            if not result.startswith('ERROR 1045 (28000): Access denied for user'):
                raise DockerException(result)
            project.mysql("CREATE DATABASE IF NOT EXISTS {name};".format(name=conf['db']['name']))
            project.mysql("CREATE USER '{user}'@'%' IDENTIFIED BY '{password}';".format(user=conf['db']['user'],
                                                                                password=conf['db']['pass']))
            project.mysql("GRANT ALL ON {name}.* TO '{user}'@'%';".format(name=conf['db']['name'],
                                                                        user=conf['db']['user']))
            project.mysql("FLUSH PRIVILEGES;")
        try:
            project.wp('core', 'download')
        except DockerCommandException as e:
            if e.args[1].find('WordPress files seem to already be present here.') == -1:
                raise e
        if os.path.exists('wordpress/wp-config.php'):
            print "wp-config.php already exist"
        else:
            project.wp('core', 'config',# '--skip-check',
            '--dbname=%s' % conf['db']['name'],
            '--dbuser=%s' % conf['db']['user'],
            '--dbpass=%s' % conf['db']['pass'],
            '--dbhost=db'
            )
        project.wp('core', 'install', '--url=%s' % conf['url'],
           '--title="%s"' % conf['name'], '--admin_email=%s' % conf['admin']['email'],
           '--admin_user=%s' % conf['admin']['user'], '--admin_password=%s' %
           conf['admin']['password'])

        project.wp('option', 'set', 'siteurl', "http://%s" % conf['url'])

        for language in conf['language']:
            if language != 'en':
                project.wp('core', 'language', 'install', language)
                project.wp('core', 'language', 'activate', language)

        if 'plugin' in conf:
            for plugin in conf['plugin']:
                project.wp('plugin', 'install', plugin)
                project.wp('plugin', 'activate', plugin)

        p = conf['project']
        # Set user UID for suexec
        if platform.system() == "Darwin":
            user_uid = 1000
        else:
            user_uid = os.getuid()
        project.docker('exec', '-ti', 'wordpress-%s' % p, 'addgroup',
                       '--gid', "%s" % user_uid, 'wordpress')
        project.docker('exec', '-ti', 'wordpress-%s' % p, 'adduser',
                       '--disabled-password', '--gecos', '""',
                       '--no-create-home', '--home', '/var/www/test',
                       '--uid', "%s" % user_uid, '--gid', "%s" % user_uid,
                       'wordpress')
        project.docker('exec', '-ti', 'wordpress-%s' % p, 'chown',
                       'wordpress:', '-R', '/var/www')
        project.docker('exec', '-ti', 'wordpress-%s' % p, 'sed',
                       '-i', "s/1000/%s/g" % user_uid,
                       '/etc/apache2/sites-available/default',)
        project.docker('exec', '-ti', 'wordpress-%s' % p, 'kill', '-HUP', '1')
        url = "http://"+project.conf['url']+"/"
        puts(colored.green("Wordpress ready : You can now go to : %s" % url))

    elif arguments['build']:

        here = os.path.dirname(__file__)
        def build_wordpress():
            args = ['build']
            if arguments['--no-cache']:
                args.append('--no-cache')
            args += ['-t', 'wordpress', os.path.join(here, 'docker',
                                                     'wordpress')]
            project.docker(*args)
        def build_mysql():
            args = ['build']
            if arguments['--no-cache']:
                args.append('--no-cache')
            args += ['-t', 'mysql', os.path.join(here, 'docker', 'mysql')]
            project.docker(*args)

        def build_sitespeed():
            args = ['build']
            if arguments['--no-cache']:
                args.append('--no-cache')
            args += ['-t', 'sitespeed', os.path.join(here, 'docker',
                                                     'sitespeed.io')]
            project.docker(*args)

        if arguments['wordpress']:
            build_wordpress()
        elif arguments['mysql']:
            build_mysql()
        elif arguments['sitespeed']:
            build_sitespeed()
        else:
            build_mysql()
            build_wordpress()
            build_sitespeed()

    elif arguments['run']:
        p = project.conf['project']
        def run_wordpress():
            if not os.path.exists('log'):
                os.mkdir('log')
            if not os.path.exists('dump'):
                os.mkdir('dump')
            project.docker('run', '--name=wordpress-%s' % p,
                           '-d', '-p', '8000:80',
                           '--hostname=wordpress.example.com',
                           '--volume' , '%s/wordpress:/var/www/test/root' % cwd,
                           '--volume', '%s/log:/var/log/apache2/' % cwd,
                           '--volume', '%s/dump:/dump/' % cwd,
                           '--link=mysql-%s:db' % p, 'wordpress')

        def run_mysql():
            project.docker('run', '--name=mysql-%s' % p, '-d',
                           '-p', '3306', 'mysql')

        if arguments['wordpress']:
            run_wordpress()
        elif arguments['mysql']:
            run_mysql()
        else:
            run_mysql()
            run_wordpress()

    elif arguments['start']:
        p = project.conf['project']
        services = project.services()
        print services
        if not 'mysql' in services:
            project.docker('start', 'mysql-%s' % p)
        if not 'wordpress' in services:
            project.docker('start', 'wordpress-%s' % p)
        url = "http://"+project.conf['url']+"/"

    elif arguments['stop']:
        p = project.conf['project']
        for service in project.services():
            project.docker('stop', '-'.join([service, p]))

    elif arguments['update']:
        project.wp('cron', 'event', 'run', 'wp_version_check')
        project.wp('cron', 'event', 'run', 'wp_update_themes')
        project.wp('cron', 'event', 'run', 'wp_update_plugins')
        project.wp('cron', 'event', 'run', 'wp_maybe_auto_update')
        project.wp('plugin', 'list', '--fields=name,version,update_version')
        project.wp('theme', 'list', '--fields=name,version,update_version')
        project.wp('core', 'check-update')

    elif arguments['upgrade']:
        project.wp('plugin', 'update', '--all')
        project.wp('theme', 'update', '--all')
        project.wp('core', 'verify-checksums')
        project.wp('core', 'update')
        project.wp('core', 'update-db')

    elif arguments['db']:
        if arguments['export']:
            contents_table = {'wp_users', 'wp_usermeta', 'wp_posts',
                              'wp_comments', 'wp_links', 'wp_postmeta',
                              'wp_terms', 'wp_term_taxonomy',
                              'wp_term_relationships', 'wp_commentmeta'}
            if arguments['--contents']:
                project.wp('db', 'export', '/dump/dump-contents.sql',
                           '--tables=%s' % ','.join(contents_table))
            elif arguments['--options']:
                project.wp('db', 'export', '/dump/dump-options.sql',
                           '--tables=wp_options')
            elif arguments['--no-contents']:
                tables = set([a[:-2] for a in
                          project.wp('db', 'tables', '--quiet').readlines()])
                tables -= contents_table
                project.wp('db', 'export', '/dump/dump-no-contents.sql',
                           '--tables=%s' % ','.join(tables))
            else:
                project.wp('db', 'export', '/dump/dump.sql')

    elif arguments['wxr']:
        if arguments['export']:
            project.wp('export', '--dir=/dump/')

    elif arguments['dictator']:
        if arguments['export']:
            project.wp('dictator', 'export', 'site', '/dump/dictator-site.yml',
                       '--force')

    elif arguments['home']:
        url = "http://"+project.conf['url']+"/"
        print "Opening : %s" % url
        webbrowser.open(url)

    elif arguments['sitespeed']:
        if not os.path.exists('sitespeed.io'):
            os.mkdir('sitespeed.io')
        project.docker('run', '--rm', '--volume', '%s/sitespeed.io:/result' % cwd, 'sitespeed', 'sitespeed.io',
                       '--screenshot', '--url', 'http://%s' % project.conf['url'],
                       '--resultBaseDir', '/result')

    else:
        print "Unknown command"
        print __doc__
        sys.exit(1)

if __name__ == '__main__':
    main()
