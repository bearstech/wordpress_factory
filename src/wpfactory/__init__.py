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
from pydoc import getdoc
from compose.cli.command import Command
from compose.cli.docker_client import docker_client
from compose.cli.main import TopLevelCommand, setup_logging, parse_doc_section
from docker.errors import APIError
from compose.cli.errors import UserError
from compose.project import NoSuchService, ConfigurationError
from compose.service import BuildError
from compose.cli.docopt_command import NoSuchCommand



import logging
from docker.client import Client
from docker import utils
import six


class ExecuteFutur(object):

    def __init__(self, client, command_id, flow):
        self.client = client
        self.command_id = command_id
        self.flow = flow

    def __iter__(self):
        return self.flow

    def wait(self):
        if six.PY3:
            return bytes().join(
                [x for x in self.client._multiplexed_buffer_helper(self.flow)]
            )
        else:
            return str().join(
                [x for x in self.client._multiplexed_buffer_helper(self.flow)]
            )

    def inspect(self):
        url = self.client._url('/exec/{0}/json'.format(self.command_id))
        res = self.client._get(url)
        self.client._raise_for_status(res)
        return res.json()

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

    return ExecuteFutur(self, cmd_id, res)


# This is monkey patch
Client.execute_return = execute_return

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

        r = c.client.execute_return(c.id, args, stream=False)
        r.wait()
        return r.inspect()

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


class WPFactoryCommand(TopLevelCommand):
    """
Wordpress factory.

    Usage:
      docker-compose [options] [COMMAND] [ARGS...]
      docker-compose -h|--help

    Options:
      --verbose                 Show more output
      --version                 Print version and exit
      -f, --file FILE           Specify an alternate compose file (default: docker-compose.yml)
      -p, --project-name NAME   Specify an alternate project name (default: directory name)

    Commands:
      init      Scaffold the project, build an empty wordpress.yml file
      build     Build or rebuild services
      help      Get help on a command
      kill      Kill containers
      logs      View output from containers
      ps        List containers
      rm        Remove stopped containers
      run       Run a one-off command
      start     Start services
      stop      Stop services
      restart   Restart services
      up        Create and start containers
      home      Open wordpress web page
      update    Search update for plugins and themes
      upgrade   Upgrade them all
      sitespeed Analyze with sitespeed.io
      mail      Open mailhog page
      dump      Dump database
      wxr       WXR exchange format

    """
    def perform_command(self, options, handler, command_options):
        if options['COMMAND'] in ['help', 'init']:
            # Skip looking up the compose file.
            handler(None, command_options)
            return
        if not os.path.exists('wordpress.yml'):
            raise Exception('You need a wordpress.yml file, try :\nwpfactory init')
        with open('wordpress.yml', 'r') as f:
            self.config = yaml.load(f)
        self._lazy_compose_conf()

        super(WPFactoryCommand, self).perform_command(options, handler, command_options)

    def _lazy_compose_conf(self):
        if not os.path.exists('docker-compose.yml'):
            if platform.system() == "Darwin":
                user_uid = 1000
            else:
                user_uid = os.getuid()
            port = self.config["url"].split(":")[1]
            fig = {
                'mailhog': {
                    'image': 'bearstech/mailhog',
                    'ports':[25, 8025],
                    'hostname': 'mail.example.com'},
                'mysql': {
                    'ports': [3306],
                    'image': 'bearstech/mysql',
                    'environment': {
                        'MYSQL_ROOT_PASSWORD': 'mypass',
                        'MYSQL_DATABASE': self.config['db']['name'],
                        'MYSQL_USER': self.config['db']['user'],
                        'MYSQL_PASSWORD': self.config['db']['pass'],
                    }
                },
                'wordpress': {
                    'image': 'bearstech/wordpress',
                    'ports': ["%s:80" % port],
                    'hostname': 'wordpress.example.com',
                    'volumes': [
                        'wordpress:/var/www/test/root',
                        'log:/var/log/apache2/',
                        'dump:/dump'
                    ],
                    'links': [
                        'mysql:db',
                        'mailhog:mail'
                    ],
                    'environment': {
                        'WORDPRESS_ID': user_uid
                    }
                }
            }
            yaml.dump(fig, open('docker-compose.yml', 'w'), explicit_start=True, default_flow_style=False)


    def init(self, _, options):
        """
        Initiliaze project.

        Usage: init
        """
        if os.path.exists('wordpress.yml'):
            raise Exception("wordpress.yml already exist.")
        else:
            cwd = os.getcwd()
            with open('wordpress.yml', 'w') as f:
                f.write(SCAFFOLD_TEMPLATE.format(project=cwd.split('/')[-1],
                                                 docker_host=guess_docker_host()))
                print "Just scaffolded the wordpress.yml file, edit it."
                # TODO [xdg-]open -e wordpress.yml

    def home(self, project, options):
        """
        Open home page.

        Usage: home
        """
        url = "http://%s/" % self.config['url']
        print "Opening : %s" % url
        webbrowser.open(url)

    def exec_(self, service, *args):
        project = self.get_project('docker-compose.yml')
        wp = project.get_service(service)

        container = wp.get_container()
        assert container.is_running
        c = docker_client()
        c._version = '1.16'

        cmd = list(args)
        print cmd
        r = c.execute_return(container.id, cmd, stream=False)
        out = r.wait()
        inspect = r.inspect()
        if inspect['ExitCode'] != 0:
            raise DockerCommandException(out)
        return out

    def wp(self, *args):
        return self.exec_('wordpress', 'wp', '--allow-root', '--path=/var/www/test/root/', *args)

    def mysql(self, sql):
        return self.exec_('wordpress', 'mysql', '-h', 'db', '-u', self.config['db']['user'],
                           '--password=%s' % self.config['db']['pass'],
                           self.config['db']['name'], '-e', sql)

    def mysql_as_root(self, sql, database=True):
        cmd = ['wordpress', 'mysql', '-h', 'db', '-u', 'root',
               '--password=mypass']
        if database:
            cmd.append(self.config['db']['name'])
        cmd += ['-e', sql]
        return self.exec_(*cmd)

    def config(self, project, options):
        """
        Configure your Wordpress

        Usage: config
        """
        conf = self.config
        try:
            o = self.mysql('SELECT 1+1;')
        except DockerCommandException as e:
            if not e.args[0].startswith('ERROR 1045 (28000): Access denied for user'):
                raise e

        if not os.path.exists('wordpress/wp-admin/index.php'):
            # Download Wordpress
            self.wp('core', 'download')

        # Configure it and install it
        if os.path.exists('wordpress/wp-config.php'):
            print "wp-config.php already exist"
        else:
            self.wp('core', 'config',# '--skip-check',
            '--dbname=%s' % conf['db']['name'],
            '--dbuser=%s' % conf['db']['user'],
            '--dbpass=%s' % conf['db']['pass'],
            '--dbhost=db'
            )
        try:
            self.wp('core', 'is-installed')
        except DockerCommandException as e:
            if e.args[0] != "":
                raise e
            self.wp('core', 'install', '--url=%s' % conf['url'],
            '--title=%s' % conf['name'], '--admin_email=%s' % conf['admin']['email'],
            '--admin_user=%s' % conf['admin']['user'], '--admin_password=%s' %
            conf['admin']['password'])

        self.wp('option', 'set', 'siteurl', "http://%s" % conf['url'])
        self.wp('option', 'set', 'blogname', conf['name'])

        for language in conf['language']:
            if language != 'en':
                self.wp('core', 'language', 'install', language)
                self.wp('core', 'language', 'activate', language)

        if 'plugin' in conf:
            for plugin in conf['plugin']:
                self.wp('plugin', 'install', plugin)
                self.wp('plugin', 'activate', plugin)

    def build(self, project, options):
        """
        Build the images

        Usage: build
        """
        c = docker_client()
        here = os.path.dirname(__file__)
        no_cache = False
        for image in ['wordpress', 'mysql', 'sitespeed', 'mailhog']:
            dockerfile = os.path.join(here, 'docker', image)
            for line in c.build(path=dockerfile, tag='bearstech/%s' % image,
                                nocache=no_cache, stream=True):
                # FIXME it's ugly, build shouldn't stream raw JSON
                l = json.loads(line)
                if "stream" in l:
                    print l['stream'],


    def update(self, project, options):
        """
        Search available updates.

        Usage: update
        """
        # FIXME the ouput is ugly
        self.wp('cron', 'event', 'run', 'wp_version_check')
        self.wp('cron', 'event', 'run', 'wp_update_themes')
        self.wp('cron', 'event', 'run', 'wp_update_plugins')
        self.wp('cron', 'event', 'run', 'wp_maybe_auto_update')
        print self.wp('plugin', 'list', '--fields=name,version,update_version')
        print self.wp('theme', 'list', '--fields=name,version,update_version')
        print self.wp('core', 'check-update')

    def upgrade(self, project, options):
        """
        Upgrade core, plugins and themes.

        Usage: upgrade
        """
        # FIXME the ouput is ugly
        print self.wp('plugin', 'update', '--all')
        print self.wp('theme', 'update', '--all')
        print self.wp('core', 'verify-checksums')
        print self.wp('core', 'update')
        print self.wp('core', 'update-db')

    def sitespeed(self, project, options):
        """
        Sitespeed.io

        Usage: sitespeed
        """
        if not os.path.exists('sitespeed.io'):
            os.mkdir('sitespeed.io')
        c = docker_client()
        cwd = os.getcwd()
        container = c.create_container(image='bearstech/sitespeed',
                           volumes=['%s/sitespeed.io:/result' % cwd],
                           command=['sitespeed.io', '--screenshot',
                                    '--url', 'http://%s' % self.config['url'],
                                    '--resultBaseDir', '/result'])
        c.start(container=container)
        for l in c.logs(container=container, stream=True):
            print l
        c.remove_container(container=container)

    def mail(self, project, options):
        """
        Mailhog

        Usage: mail
        """
        project = self.get_project('docker-compose.yml')
        port = project.get_service('mailhog').get_container().inspect()["NetworkSettings"]["Ports"]["8025/tcp"][0]["HostPort"]
        url = "http://%s:%s" % (guess_docker_host(), port)
        print "Opening : %s" % url
        webbrowser.open(url)

    def dump(self, project, options):
        """
        Database

        Usage: dump (content|option|all)

        """
        contents_table = {'wp_users', 'wp_usermeta', 'wp_posts', 'wp_comments',
                          'wp_links', 'wp_postmeta', 'wp_terms',
                          'wp_term_taxonomy', 'wp_term_relationships',
                          'wp_commentmeta'}
        if options['content']:
            self.wp('db', 'export', '/dump/dump-contents.sql',
                        '--tables=%s' % ','.join(contents_table))
        elif options['option']:
            self.wp('db', 'export', '/dump/dump-options.sql',
                        '--tables=wp_options')
        elif options['all']:
            self.wp('db', 'export', '/dump/dump.sql')
        else:
            raise Exception()

    def wxr(self, project, options):
        """
        WXR exchange file format

        Usage: wxr export
        """
        if options['export']:
            self.wp('export', '--dir=/dump/')


log = logging.getLogger(__name__)

def main():
    setup_logging()
    try:
        command = WPFactoryCommand()
        command.sys_dispatch()
    except KeyboardInterrupt:
        log.error("\nAborting.")
        sys.exit(1)
    except (UserError, NoSuchService, ConfigurationError) as e:
        log.error(e.msg)
        sys.exit(1)
    except NoSuchCommand as e:
        log.error("No such command: %s", e.command)
        log.error("")
        log.error("\n".join(parse_doc_section("commands:", getdoc(e.supercommand))))
        sys.exit(1)
    except APIError as e:
        log.error(e.explanation)
        sys.exit(1)
    except BuildError as e:
        log.error("Service '%s' failed to build: %s" % (e.service.name, e.reason))
        sys.exit(1)



def _main():
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
        pass

    elif arguments['dictator']:
        if arguments['export']:
            project.wp('dictator', 'export', 'site', '/dump/dictator-site.yml',
                       '--force')

    else:
        print "Unknown command"
        print __doc__
        sys.exit(1)

if __name__ == '__main__':
    main()
