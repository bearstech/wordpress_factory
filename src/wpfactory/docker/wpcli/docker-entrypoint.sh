#!/bin/bash
set -e

if [ "$1" = 'wp' ]; then
	# read DATADIR from the MySQL config
	DATADIR="$("$@" --verbose --help 2>/dev/null | awk '$1 == "datadir" { print $2; exit }')"

	if [ ! -f "$WP_CLI_CONFIG_PATH" ]; then
		cat $WP_CLI_CONFIG_PATH <<-EOF
		---
		path: $WP_CLI_ROOT_PATH
		require:
			- /opt/dictator/dictator.php
		EOF
	fi
	exec "$@"

fi

exec "$@"
