Wordpress factory
=================

Prepare your containers

    docker build -t wordpress docker/wordpress
    docker build -t mysql docker/mysql

Scaffolding

    ./wpfactory scaffold

Modify the wordpress.yml file

Start services

    ./wpfactory start mysql
    ./wpfactory start wordpress

Initialize wordpress

    ./wpfactory init
