#!/usr/bin/env python
# encoding:utf8

"""
Wordpress factory.

Usage:
    wpfactory scaffold
    wpfactory init
    wpfactory start
    wpfactory start mysql
    wpfactory start wordpress
    wpfactory build mysql
    wpfactory build wordpress

Options:
    --json                         Json output
"""

__version__ = '0.1'

from subprocess import Popen, PIPE
import sys
import yaml
from cStringIO import StringIO


def docker(*args):
    print " ".join(['docker'] + list(args))
    p = Popen(['docker'] + list(args), stdout=PIPE, stderr=PIPE)
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
    args = ['exec', '-ti', 'wordpress', 'mysql', '-h', 'db', '--password=mypass', '-e'] + list(args)
    return docker(*args)

if __name__ == '__main__':
    from docopt import docopt
    import os
    import os.path

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
admin:
    email: admin@example.lan
    user: admin
    password: password
db:
    name: test
    user: test
    pass: password
""")

    if arguments['init']:
        with open('wordpress.yml', 'r') as f:
            conf = yaml.load(f)
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
        apache = """
<VirtualHost *:80>
    ServerName {name}

    DocumentRoot /var/www/test/root

    <Directory   /var/www/test/root>
        # Exec .php scripts via FastCGI:
        Options +ExecCGI

        # Acceptable overrides:
        # - FileInfo (.htacces-based rewrite rules)
        # - AuthConfig (.htaccess-based basic auth)
        AllowOverride All
    </Directory>

    ErrorLog  /var/log/apache2/{name}/error.log
    CustomLog /var/log/apache2/{name}/access.log combined
</VirtualHost>
""".format(name=conf['url'].split(':')[0])
        docker('exec', '-ti', 'wordpress', 'echo', apache, '>', '/etc/apache2/sites-available/website.conf')
        docker('restart', 'wordpress')

    if arguments['build']:
        if arguments['wordpress']:
            docker('build', '-t', 'wordpress', './docker/wordpress')
        if arguments['mysql']:
            docker('build', '-t', 'wordpress', './docker/wordpress')

    if arguments['start']:
        if arguments['wordpress']:
            pid = docker('run',  '--name=wordpress', '-d', '-p', '8000:80',
                         '--volume' , '%s/wordpress:/var/www/test/root' % cwd,
                         '--link=mysql:db', 'wordpress')
            with open('%s/wp.pid' % cwd, 'w') as f:
                f.write(pid)
        elif arguments['mysql']:
            docker('run', '--name=mysql', '-d', '-p', '3306', 'mysql')
        else:
            pass

