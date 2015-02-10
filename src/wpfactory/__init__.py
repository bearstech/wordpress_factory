#!/usr/bin/env python
# encoding:utf8

__version__ = '0.3'

import os
import sys
import os.path
import webbrowser
import platform
import json
from pydoc import getdoc
import logging

import yaml
# FIXME bring back the colors
# from clint.textui import colored, puts

from compose.cli.docker_client import docker_client
from compose.cli.main import TopLevelCommand, setup_logging, parse_doc_section
from docker.errors import APIError
from compose.cli.errors import UserError
from compose.project import NoSuchService, ConfigurationError
from compose.service import BuildError
from compose.cli.docopt_command import NoSuchCommand

log = logging.getLogger(__name__)
hdl = logging.StreamHandler()
logger = logging.getLogger('compose.cli.command')
logger.addHandler(hdl)


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
      wpfactory [options] [COMMAND] [ARGS...]
      wpfactory -h|--help

    Options:
      --verbose                 Show more output
      --version                 Print version and exit
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
      dictator  Dictator flat configuration
      doctor    Checkup for broken factory

    """
    def perform_command(self, options, handler, command_options):
        if options['COMMAND'] in ['help', 'init']:
            # Skip looking up the compose file.
            handler(None, command_options)
            return
        if not os.path.exists('wordpress.yml'):
            raise Exception('''You need a wordpress.yml file, try :
wpfactory init''')
        with open('wordpress.yml', 'r') as f:
            self.config = yaml.load(f)
        self._lazy_compose_conf()

        super(WPFactoryCommand, self).perform_command(options, handler,
                                                      command_options)

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
                    'ports': [25, 8025],
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
            yaml.dump(fig, open('docker-compose.yml', 'w'), explicit_start=True,
                      default_flow_style=False)

    def exec_(self, service, *args):
        project = self.get_project('docker-compose.yml')
        wp = project.get_service(service)

        container = wp.get_container()
        assert container.is_running
        c = docker_client()
        c._version = '1.15'


        # Because we can't get status code from exec in 1.15, here come da
        # shitty fix
        inner_cmd = " ".join(list(args))
        print inner_cmd
        inner_cmd += "&& echo OK || echo NOPE"
        cmd = ['sh', '-c', "%s" %inner_cmd]

        r = c.execute(container.id, cmd, stream=True)
        out = [l for l in r]
        if not "OK\n" in out:
            command_result = ''.join(out)
            log.error(command_result)
            raise DockerCommandException("Command exited with non null status")
        return out

    def wp(self, *args):
        return self.exec_('wordpress', 'wp', '--allow-root',
                          '--path=/var/www/test/root/', *args)

    def mysql(self, sql):
        return self.exec_('wordpress', 'mysql', '-h', 'db',
                          '-u', self.config['db']['user'],
                          '--password=%s' % self.config['db']['pass'],
                          self.config['db']['name'], '-e', '"%s"' % sql)

    def mysql_as_root(self, sql, database=True):
        cmd = ['wordpress', 'mysql', '-h', 'db', '-u', 'root',
               '--password=mypass']
        if database:
            cmd.append(self.config['db']['name'])
        cmd += ['-e', sql]
        return self.exec_(*cmd)

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

    def config(self, project, options):
        """
        Configure your Wordpress

        Usage: config
        """
        conf = self.config
        try:
            self.mysql('SELECT 1+1;')
        except DockerCommandException as e:
            if not e.args[0].startswith(
                    'ERROR 1045 (28000): Access denied for user'):
                raise e
            # FIXME what happens if the DB is not ready?

        if not os.path.exists('wordpress/wp-admin/index.php'):
            # Download Wordpress
            self.wp('core', 'download')

        # Configure it and install it
        if os.path.exists('wordpress/wp-config.php'):
            print "wp-config.php already exist"
        else:
            self.wp('core', 'config',  # '--skip-check',
                    '--dbname=%s' % conf['db']['name'],
                    '--dbuser=%s' % conf['db']['user'],
                    '--dbpass=%s' % conf['db']['pass'],
                    '--dbhost=db'
                    )
        try:
            self.wp('core', 'is-installed')
        except DockerCommandException as e:
            self.wp('core', 'install', '--url=%s' % conf['url'],
                    '--title="%s"' % conf['name'],
                    '--admin_email=%s' % conf['admin']['email'],
                    '--admin_user=%s' % conf['admin']['user'],
                    '--admin_password=%s' % conf['admin']['password'])

        self.wp('option', 'set', 'siteurl', "http://%s" % conf['url'])
        self.wp('option', 'set', 'blogname', '"%s"' % conf['name'])

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
                                       volumes=[
                                           '%s/sitespeed.io:/result' % cwd],
                                       command=['sitespeed.io', '--screenshot',
                                                '--url',
                                                'http://%s' % self.config['url'],
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
        port = project.get_service('mailhog').get_container().inspect()[
            "NetworkSettings"]["Ports"]["8025/tcp"][0]["HostPort"]
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

    def dictator(self, project, options):
        """
        Dictator

        Usage: dictator export
        """
        # FIXME configure the wp-cli plugin path
        if options['export']:
            self.wp('dictator', 'export', 'site', '/dump/dictator-site.yml',
                    '--force')

    def doctor(self, project, options):
        """
        Doctor

        Usage: doctor
        """
        c = docker_client()
        assert "OK" == c.ping()
        if utils.compare_version('1.15', c.version()['ApiVersion']) < 0:
            raise Exception('Your docker is too old.')
        if os.path.exists('docker-compose.yml'):
            os.unlink('docker-compose.yml')
        self._lazy_compose_conf()
        project = self.get_project('docker-compose.yml')
        for name in ['wordpress', 'mailhog', 'mysql']:
            service = project.get_service(name)
            container = service.get_container()
            assert container.is_running
            if name == "wordpress":
                os.path.abspath('wordpress') == \
                    container.inspect()['Volumes']['/var/www/test/root']
        print "Everything looks ok."


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
        log.error("\n".join(parse_doc_section("commands:",
                                              getdoc(e.supercommand))))
        sys.exit(1)
    except APIError as e:
        log.error(e.explanation)
        sys.exit(1)
    except BuildError as e:
        log.error("Service '%s' failed to build: %s" %
                  (e.service.name, e.reason))
        sys.exit(1)

if __name__ == '__main__':
    main()
