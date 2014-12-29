#!/bin/sh

docker exec -ti `cat wp.pid` ./wp-cli.phar --allow-root --path=/var/www/test/root plugin update --all
docker exec -ti `cat wp.pid` ./wp-cli.phar --allow-root --path=/var/www/test/root theme update --all
docker exec -ti `cat wp.pid` ./wp-cli.phar --allow-root --path=/var/www/test/root core verify-checksums
docker exec -ti `cat wp.pid` ./wp-cli.phar --allow-root --path=/var/www/test/root core update
docker exec -ti `cat wp.pid` ./wp-cli.phar --allow-root --path=/var/www/test/root core update-db


