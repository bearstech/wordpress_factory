#!/bin/sh

docker run --name=wordpress -d -p 8000:80 --volume `pwd`/src/wordpress/:/var/www/test/root --link=mysql:db wordpress > wp.pid
