FROM debian:wheezy

# Base system
RUN apt-get update && apt-get -y install php5-cgi \
    php5-mysql apache2-mpm-worker apache2-suexec libapache2-mod-fcgid php-apc \
    php5-memcached php5-curl php5-gd php5-intl php-pear php5-imagick \
    php5-imap php5-mcrypt php5-cli less wget mysql-client curl python git \
    && rm -r /var/lib/apt/lists/*
ADD website.conf /etc/apache2/sites-available/default
ADD fcgid.conf /etc/apache2/mods-available/
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

ADD https://raw.githubusercontent.com/bearstech/phptop/wp/phptop_hook.php /usr/share/phptop/
ADD https://raw.githubusercontent.com/bearstech/phptop/master/debian/phptop.ini etc/php5/conf.d/

ADD php5-cgi /var/www/suexec/wordpress/
RUN chmod 700 /var/www/suexec/wordpress/php5-cgi && \
    chmod +r /usr/share/phptop/phptop_hook.php /etc/php5/conf.d/phptop.ini
WORKDIR /root

EXPOSE 80

VOLUME /var/www/test/root
CMD apachectl -d /etc/apache2 -f apache2.conf -e info -DFOREGROUND
