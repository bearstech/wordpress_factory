#!/bin/sh

WP=`cat wp.pid`
CLI='./wp-cli.phar --allow-root --path=/var/www/test/root'

docker exec -ti $WP $CLI cron event run wp_version_check
docker exec -ti $WP $CLI cron event run wp_update_themes
docker exec -ti $WP $CLI cron event run wp_update_plugins
docker exec -ti $WP $CLI cron event run wp_maybe_auto_update
docker exec -ti $WP $CLI plugin list --fields=name,version,update_version
docker exec -ti $WP $CLI theme list --fields=name,version,update_version
docker exec -ti $WP $CLI core check-update
