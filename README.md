Wordpress factory
=================

A factory to prepare, deploy, upgrade your Wordpress.

No more MAMP, XAMP and other strange tools.
Your Worpdress runs on a Linux, the same used in production, you work with your tool, and deploy as usual.

The magic
---------

This is no magic. Wordpress factory is just a wrapper of
[Docker compose](https://github.com/docker/fig) and [wp-cli](http://wp-cli.org/).
Data stays on your hard drive, action are done in Docker (and inside a virtualbox, if you are using Mac OSX).

Install
-------

You need python and virtualenv to build the application,
[docker](https://www.docker.com/) (>=1.3) (local or [boot2docker](http://boot2docker.io/)) to use it.

### Local install

    make install

The application is in ./bin/wpfactory

Demo time
---------

Scaffolding

    ./wpfactory init

Modify the wordpress.yml file

Prepare your containers

    ./wpfactory build

Start services

    ./wpfactory up

Configure your wordpress

    ./wpfactory config

Wordpress is now running, in port 8000, localhost for linux, ask boot2docker on a Mac :

    ./wpfactory home

Licence
-------

GPL v3, © 2014 Mathieu Lecarme.
