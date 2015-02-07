#!/bin/bash

ARGUMENTS="memcached -l 0.0.0.0 -p 11211 -m 64 -u nobody -v"
if [ "$MEMCACHED_USER" ]; then
    echo $MEMCACHED_PASSWORD | saslpasswd2 -c -p -a memcached $MEMCACHED_USER
    ARGUMENTS="$ARGUMENTS -B binary -S"
fi
echo $ARGUMENTS > /start-memcached
chmod +x /start-memcached

exec "$@"
