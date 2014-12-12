FROM debian:wheezy

RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y install php5-cgi php5-mysql apache2-mpm-worker apache2-suexec \
    libapache2-mod-fcgid php-apc php5-memcached php5-curl php5-gd php5-intl \
    php-pear php5-imagick php5-imap php5-mcrypt php5-cli
RUN mkdir -p /var/log/apache2/test.example.com
ADD website.conf /etc/apache2/sites-available/
RUN ln -s /etc/apache2/sites-available/website.conf /etc/apache2/sites-enabled/
ADD fcgid.conf /etc/apache2/mods-available/

RUN mkdir /opt/wpcli
ADD https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar /opt/wpcli/
RUN chmod +x /opt/wpcli/wp-cli.phar
RUN ln -s /opt/wpcli/wp-cli.phar /usr/local/bin/wp

EXPOSE 80

VOLUME /var/www/test/root
CMD apachectl -d /etc/apache2 -f apache2.conf -e info -DFOREGROUND
