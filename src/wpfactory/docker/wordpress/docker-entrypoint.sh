#!/bin/bash

id wordpress 2> /dev/null
if [ $? -eq 0 ]; then
    echo "Wordpress user already created."
else
    if [ -z ${WORDPRESS_ID+x} ]; then
        WORDPRESS_ID=1000
    fi
    groupadd --gid $WORDPRESS_ID wordpress
    adduser --disabled-password --gecos "" --no-create-home \
        --home /var/www/test --uid $WORDPRESS_ID --gid $WORDPRESS_ID wordpress
    chown wordpress: -R /var/www
    sed -i "s/1000/$WORDPRESS_ID/g" /etc/apache2/sites-available/default
    echo "Wordpress user created."
fi
exec "$@"
