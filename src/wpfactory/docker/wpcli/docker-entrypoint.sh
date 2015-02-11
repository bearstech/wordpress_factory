#!/bin/bash
set -e

if [ "$1" = 'wp' ]; then
	if [ ! -f "$WP_CLI_CONFIG_PATH" ]; then
		cat <<-EOF > $WP_CLI_CONFIG_PATH
		---
		path: $WP_CLI_ROOT_PATH
		require:
		    - /opt/dictator/dictator.php
		core config:
		    dbuser: $DB_ENV_MYSQL_USER
		    dbpass: $DB_ENV_MYSQL_PASSWORD
		    dbname: $DB_ENV_MYSQL_DATABASE
		    dbhost: $DB_PORT_3306_TCP_ADDR
		EOF
	fi
	exec "$@"

fi

exec "$@"
