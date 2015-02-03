#!/usr/bin/env python
# encoding:utf8

"""
Wordpress factory.

Usage:
    wpfactory scaffold
    wpfactory build [mysql|wordpress|sitespeed|mailhog] [--no-cache]
    wpfactory run [mysql|wordpress|mailhog] [--docker]
    wpfactory start
    wpfactory stop
    wpfactory config
    wpfactory update
    wpfactory upgrade
    wpfactory db export [--contents|--no-contents|--options]
    wpfactory wxr export
    wpfactory dictator export
    wpfactory home
    wpfactory mail
    wpfactory sitespeed
    wpfactory fig.yml
    wpfactory test
    wpfactory

Options:
    -h --help   Show this screen.
    --json      Json output
    --no-wxr    Export all except WXR stuff
"""

__version__ = '0.2'

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
import json
from compose.cli.command import Command
from compose.cli.docker_client import docker_client
import logging
import dockerpty
from docker.client import Client
from docker import utils
import six


def execute_return(self, container, cmd, detach=False, stdout=True, stderr=True,
            stream=False, tty=False):
    if utils.compare_version('1.15', self._version) < 0:
        raise errors.APIError('Exec is not supported in API < 1.15')
    if isinstance(container, dict):
        container = container.get('Id')
    if isinstance(cmd, six.string_types):
        cmd = shlex.split(str(cmd))

    data = {
        'Container': container,
        'User': '',
        'Privileged': False,
        'Tty': tty,
        'AttachStdin': False,
        'AttachStdout': stdout,
        'AttachStderr': stderr,
        'Detach': detach,
        'Cmd': cmd
    }

    # create the command
    url = self._url('/containers/{0}/exec'.format(container))
    res = self._post_json(url, data=data)
    self._raise_for_status(res)

    # start the command
    cmd_id = res.json().get('Id')
    res = self._post_json(self._url('/exec/{0}/start'.format(cmd_id)),
                        data=data, stream=stream)
    self._raise_for_status(res)
    if stream:
        return cmd_id, self._multiplexed_socket_stream_helper(res)
    elif six.PY3:
        return cmd_id, bytes().join(
            [x for x in self._multiplexed_buffer_helper(res)]
        )
    else:
        return cmd_id, str().join(
            [x for x in self._multiplexed_buffer_helper(res)]
        )

# This is monkey patch
Client.execute_return = execute_return

def execute_inspect(self, id):
    url = self._url('/exec/{0}/json'.format(id))
    res = self._get(url)
    self._raise_for_status(res)
    return res.json()

Client.execute_inspect = execute_inspect



hdl = logging.StreamHandler()
logger = logging.getLogger('compose.cli.command')
logger.addHandler(hdl)


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
    """Contains our project configuration and methods to execute some commands
    in our dockers
    """

    def __init__(self):
        self._project = None
        if not os.path.exists('wordpress.yml'):
            print __doc__
            error("Can't find wordpress.yml file, use:\n$ wpfactory scaffold\nand edit it." )
        with open('wordpress.yml', 'r') as f:
            self.conf = yaml.load(f)

    def get_client(self):
        c = docker_client()
        c._version = '1.16'
        return c

    def get_project(self):
        if self._project is None:
            c = Command()
            cfg = c.get_config_path()
            self._project = c.get_project(cfg)
        return self._project

    def get_container(self, name):
        c = self.get_project().get_service(name).get_container()
        c.client._version = '1.16' # Monkey patch, Docker > 1.2
        return c

    def execute(self, service, *args):
        c = self.get_container(service)

        cid, r = c.client.execute_return(c.id, args, stream=False)
        r = c.client.execute_inspect(cid)
        return r

    def docker(self, *args, **opts):
        """Execute a Docker command
        """
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
        """Execute a wp-cli command inside wordpress's docker
        """
        return self.get_container('wordpress').client.execute([
            'wp', '--allow-root', '--path=/var/www/test/root',
            '--require=/opt/dictator/dictator.php'] + list(args))

    def mysql(self, *args):
        """Execute a mysql command inside wordpress's docker
        """
        return self.get_container('wordpress').client.execute(['mysql', '-h',
                                                               'db', '--password=mypass', '-e'] + list(args))

    def services(self):
        "Started services."
        s = set()
        project = self.conf['project']
        for service in [SPACES.split(ps)[:-1][-1] for ps in
                        self.docker('ps').readlines()[1:]]:
            if service.split('-')[-1] == project:
                s.add(service[:-(len(project)+1)])
        return s

    def build(self, name, no_cache=False):
        here = os.path.dirname(__file__)
        dockerfile = os.path.join(here, 'docker', name)
        return self.get_client().build(path=dockerfile, tag='bearstech/%s' % name,
                                nocache=no_cache)

    def inspect(self, name):
        return self.get_container(name).inspect()


def guess_docker_host():
        d = os.environ.get('DOCKER_HOST', None)
        if d:
            return d.split('//')[-1].split(':')[0]
        else:
            return "localhost"


def main():
    """
    """
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

        # First step in our configuration, create users and tables for our wordpress

        create_user = False # Dirty but efficient because...
        try:
            r = project.docker('exec', '-ti', 'wordpress-%s' % conf['project'],
                       'mysql', '-h', 'db', '-u', conf['db']['user'],
                       '--password=%s' % conf['db']['pass'],
                       conf['db']['name'], '-e', 'SELECT 1+1;')
        except DockerCommandException as e:
            # ...Sometimes cmd errors will propagate to docker exec
            if not e.args[1].startswith('ERROR 1045 (28000): Access denied for user'):
                raise e
            create_user = True
        else:
            result = r.read()
            if "ERROR" in result:
                # ...Sometimes docker exec will return 0 but the cmd failed
                if not result.startswith('ERROR 1045 (28000): Access denied for user'):
                    raise DockerException(result)
                create_user = True
        if create_user:
            project.mysql("CREATE DATABASE IF NOT EXISTS {name};".format(name=conf['db']['name']))
            project.mysql("CREATE USER '{user}'@'%' IDENTIFIED BY '{password}';".format(user=conf['db']['user'],
                                                                                password=conf['db']['pass']))
            project.mysql("GRANT ALL ON {name}.* TO '{user}'@'%';".format(name=conf['db']['name'],
                                                                        user=conf['db']['user']))
            project.mysql("FLUSH PRIVILEGES;")

        # Second step : wp-cli commands
        # Download Wordpress
        try:
            project.wp('core', 'download')
        except DockerCommandException as e:
            if e.args[1].find('WordPress files seem to already be present here.') == -1:
                raise e
        # Configure it and install it
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
           '--title=%s' % conf['name'], '--admin_email=%s' % conf['admin']['email'],
           '--admin_user=%s' % conf['admin']['user'], '--admin_password=%s' %
           conf['admin']['password'])

        project.wp('option', 'set', 'siteurl', "http://%s" % conf['url'])
        project.wp('option', 'set', 'blogname', conf['name'])

        for language in conf['language']:
            if language != 'en':
                project.wp('core', 'language', 'install', language)
                project.wp('core', 'language', 'activate', language)

        if 'plugin' in conf:
            for plugin in conf['plugin']:
                project.wp('plugin', 'install', plugin)
                project.wp('plugin', 'activate', plugin)

        p = conf['project']

        # Third Step : create a user in our docker with the same user as our
        # host
        # So, the docker volume UID == curent user and he will be happy to edit
        # some code, weeee !

        # Set user UID for suexec
        if platform.system() == "Darwin":
            user_uid = 1000
        else:
            user_uid = os.getuid()
        create_user = True # XXX Yeah... Again...
        try:
            i = project.docker('exec', '-ti', 'wordpress-%s' % p, 'id', 'wordpress')
        except DockerCommandException as e:
            if not e.args[1].startswith('id: wordpress: No such user'):
                raise e
        else:
            if i.read().startswith('uid={uid}(wordpress)'.format(uid=user_uid) ):
                print "User wordpress already exists."
                create_user = False
        if create_user:
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

        # Now restart our apache
        project.docker('exec', '-ti', 'wordpress-%s' % p, 'kill', '-HUP', '1')
        url = "http://"+project.conf['url']+"/"
        puts(colored.green("Wordpress ready : You can now go to : %s" % url))

    elif arguments['build']:
        # Ask docker to build all our Dockerfiles

        no_cache = arguments['--no-cache']
        if arguments['wordpress']:
            project.build('wordpress', no_cache)
        elif arguments['mysql']:
            project.build('mysql', no_cache)
        elif arguments['sitespeed']:
            project.build('sitespeed', no_cache)
        elif arguments['mailhog']:
            project.build('mailhog', no_cache)
        else:
            project.build('wordpress', no_cache)
            project.build('mysql', no_cache)
            project.build('sitespeed', no_cache)
            project.build('mailhog', no_cache)

    elif arguments['run']:
        # Create our containers and run it
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
                           '--link=mailhog:mail',
                           '--link=mysql-%s:db' % p, 'bearstech/wordpress')

        def run_mysql():
            if arguments['--docker']:
                project.docker('run', '--name=mysql-%s' % p, '-d', '-e',
                               'MYSQL_ROOT_PASSWORD=mypass','mysql')
            else:
                project.docker('run', '--name=mysql-%s' % p, '-d',
                               '-p', '3306', 'bearstech/mysql')

        def run_mailhog():
            project.docker('run', '--name=mailhog', '-d', '-p', '8025',
                           '-p', '25',
                           '--hostname=mail.example.com', 'bearstech/mailhog')
        if arguments['wordpress']:
            run_wordpress()
        elif arguments['mysql']:
            run_mysql()
        elif arguments['mailhog']:
            run_mailhog()
        else:
            run_mysql()
            run_mailhog()
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
        project.docker('run', '--rm', '--volume', '%s/sitespeed.io:/result' % cwd, 'bearstech/sitespeed', 'sitespeed.io',
                       '--screenshot', '--url', 'http://%s' % project.conf['url'],
                       '--resultBaseDir', '/result')

    elif arguments['mail']:
        port = project.inspect('mailhog')["NetworkSettings"]["Ports"]["8025/tcp"][0]["HostPort"]
        url = "http://%s:%s" % (guess_docker_host(), port)
        print "Opening : %s" % url
        webbrowser.open(url)

    elif arguments['fig.yml']:
        fig = {
            'mailhog': {
                'image': 'bearstech/mailhog',
                'ports':[25, 8025],
                'hostname': 'mail.example.com'},
            'mysql': {
                'ports': [3306],
                'image': 'bearstech/mysql'
            },
            'wordpress': {
                'image': 'bearstech/wordpress',
                'ports': [80],
                'hostname': 'wordpress.example.com',
                'volumes': [
                    'wordpress:/var/www/test/root',
                    'log:/var/log/apache2/',
                    'dump:/dump'
                ],
                'links': [
                    'mysql:db',
                    'mailhog:mail'
                ]
            }
        }
        yaml.dump(fig, open('fig.yml', 'w'), explicit_start=True, default_flow_style=False)

    elif arguments['test']:
        w = project.execute('wordpress', 'oups', 'aux')
        print w
        w = project.execute('wordpress', 'ps', 'aux')
        print w

    else:
        print "Unknown command"
        print __doc__
        sys.exit(1)

if __name__ == '__main__':
    main()
