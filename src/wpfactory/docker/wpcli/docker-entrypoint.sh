#!/bin/bash
set -e

if [ "$1" = 'wp' ]; then
	if [ ! -f "$WP_CLI_CONFIG_PATH" ]; then
		cat <<-EOF > $WP_CLI_CONFIG_PATH
		---
		path: $WP_CLI_ROOT_PATH
		require:
		    - /opt/dictator/dictator.php
		EOF
	fi
	exec "$@"

fi

exec "$@"
