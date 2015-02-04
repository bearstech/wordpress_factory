FROM debian:wheezy

# Base system
RUN apt-get update && apt-get -y install php5-cgi \
    php5-mysql apache2-mpm-worker apache2-suexec libapache2-mod-fcgid php-apc \
    php5-memcached php5-curl php5-gd php5-intl php-pear php5-imagick adduser\
    php5-imap php5-mcrypt php5-cli less wget mysql-client curl python git ssmtp \
    && rm -r /var/lib/apt/lists/*
COPY website.conf /etc/apache2/sites-available/default
COPY fcgid.conf /etc/apache2/mods-available/
RUN a2enmod suexec


RUN mkdir -p /opt/wpcli /usr/share/phptop /var/www/suexec/wordpress

WORKDIR /opt/wpcli
# too many redirection for an ADD
RUN wget https://github.com/wp-cli/wp-cli/releases/download/v0.18.0/wp-cli-0.18.0.phar -O wp-cli.phar
RUN chmod +x wp-cli.phar && \
    ln -s /opt/wpcli/wp-cli.phar /usr/local/bin/wp
#RUN mkdir -p /root/.wp-cli/
#ADD wp-cli.yml /root/.wp-cli/config.yml

WORKDIR /opt/
RUN git clone https://github.com/danielbachhuber/dictator.git

RUN wget https://raw.githubusercontent.com/bearstech/phptop/wp/phptop_hook.php -O /usr/share/phptop/phptop_hook.php
RUN wget https://raw.githubusercontent.com/bearstech/phptop/master/debian/phptop.ini -O /etc/php5/conf.d/phptop.ini

COPY php5-cgi /var/www/suexec/wordpress/
RUN chmod 700 /var/www/suexec/wordpress/php5-cgi && \
    chmod +r /usr/share/phptop/phptop_hook.php /etc/php5/conf.d/phptop.ini

COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

EXPOSE 80

VOLUME /var/www/test/root
CMD apachectl -d /etc/apache2 -f apache2.conf -e info -DFOREGROUND
