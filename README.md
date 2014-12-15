Wordpress factory
=================


    docker build -t wordpress wordpress
    docker build -t mysql mysql
    docker run -d --name=mysql mysql
    ./start_wordpress.sh
    docker exec `cat wp.pid` factory site
