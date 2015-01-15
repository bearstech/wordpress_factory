Wordpress factory
=================

A factory to prepare, deploy, upgrade your Wordpress

No more LAMP, XAMP and other strange tools.
Your Worpdress runs on a Linux, the same used in production, and you work with your tool, and deploy as usual.

The magic
---------

The is no magic. Wordpress factory is just a wrapper of Docker and wp-cli.
Data stays on your hard drive, action are done in Docker.
Your docker if you are using Linux, or inside a virtualbox, if you are using Mac OSX.

Install
-------

You need python and virtualenv to build the application,
[docker](https://www.docker.com/) (local or [boot2docker](http://boot2docker.io/)) to use it.

### Local install

    make install

The application is in ./bin/wpfactory

### PEX install

You can build a package, to handle all parts of the install, and distribute it

    make pex

Enjoy your `wpfactory` file.

Demo time
---------

Prepare your containers

    ./wpfactory build wordpress
    ./wpfactory build mysql

Scaffolding

    ./wpfactory scaffold

Modify the wordpress.yml file

Start services

    ./wpfactory run mysql
    ./wpfactory run wordpress

Configure your wordpress

    ./wpfactory config

Wordpress is no running, in port 8000, localhost for linux, ask boot2docker on a Mac :

    boot2docker ip

Licence
-------

GPL v3, © 2014 Mathieu Lecarme.
