#!/bin/bash

# FIXME -u memcache
ARGUMENTS="memcached -l 0.0.0.0 -p 11211 -m 64 -u root -v"
if [ "$MEMCACHED_USER" ]; then
    echo "START=yes" >> /etc/default/saslauthd
    /etc/init.d/saslauthd start
    echo $MEMCACHED_PASSWORD | saslpasswd2 -c -p -a memcached $MEMCACHED_USER
    ARGUMENTS="$ARGUMENTS -B binary -S"
    echo "Adding user $MEMCACHED_USER"
fi
echo $ARGUMENTS > /start-memcached
chmod +x /start-memcached
echo $ARGUMENTS

exec "$@"
