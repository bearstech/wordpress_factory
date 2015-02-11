#!/bin/bash
set -e

if [ "$1" = 'wp' ]; then
	if [ ! -f "$WP_CLI_CONFIG_PATH" ]; then
		cat <<-EOF > $WP_CLI_CONFIG_PATH
		---
		path: $WP_CLI_ROOT_PATH
		url: $WP_ENV_WORDPRESS_SITE_URL
		require:
		    - /opt/dictator/dictator.php
		core config:
		    dbuser: $DB_ENV_MYSQL_USER
		    dbpass: $DB_ENV_MYSQL_PASSWORD
		    dbname: $DB_ENV_MYSQL_DATABASE
		    dbhost: $DB_PORT_3306_TCP_ADDR
		core install:
		    title: $WP_ENV_WORDPRESS_TITLE
		    admin_email: $WP_ENV_WORDPRESS_ADMIN_EMAIL
		    admin_user: $WP_ENV_WORDPRESS_ADMIN_USER
		    admin_password: $WP_ENV_WORDPRESS_ADMIN_PASSWORD
		EOF
	fi
	if [ ! -f "$WP_CLI_ROOT_PATH/wp-cron.php" ]; then
        wp core download
    fi
	if [ ! -f "$WP_CLI_ROOT_PATH/wp-config.php" ]; then
        wp core config
    fi
    if ! wp core is-installed; then
        wp core install
        #wp option set blogname "$WP_ENV_WORDPRESS_BLOGNAME"
        for element in $WP_ENV_WORDPRESS_LANGUAGE; do
            if [ $element != "en" ]; then
                wp core language install $element
                wp core language activate $element
            fi
        done
    fi
	exec "$@"

fi

exec "$@"
