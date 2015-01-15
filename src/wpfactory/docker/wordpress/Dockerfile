FROM debian:wheezy

RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y install php5-cgi php5-mysql apache2-mpm-worker apache2-suexec \
    libapache2-mod-fcgid php-apc php5-memcached php5-curl php5-gd php5-intl \
    php-pear php5-imagick php5-imap php5-mcrypt php5-cli less wget mysql-client python git
RUN mkdir -p /var/log/apache2/test.example.com
ADD website_conf.py /opt/website_conf.py
RUN /usr/bin/python /opt/website_conf.py test.example.com
RUN ln -s /etc/apache2/sites-available/website.conf /etc/apache2/sites-enabled/
ADD fcgid.conf /etc/apache2/mods-available/

RUN mkdir -p /opt/wpcli
WORKDIR /opt/wpcli
# too many redirection for an ADD
RUN wget https://github.com/wp-cli/wp-cli/releases/download/v0.17.1/wp-cli.phar
RUN chmod +x wp-cli.phar
RUN ln -s /opt/wpcli/wp-cli.phar /usr/local/bin/wp
RUN mkdir -p /root/.wp-cli/
ADD wp-cli.yml /root/.wp-cli/config.yml

WORKDIR /opt/
RUN git clone https://github.com/danielbachhuber/dictator.git

RUN mkdir -p /usr/share/phptop
ADD https://raw.githubusercontent.com/bearstech/phptop/wp/phptop_hook.php /usr/share/phptop/
RUN chmod +r /usr/share/phptop/phptop_hook.php
ADD https://raw.githubusercontent.com/bearstech/phptop/master/debian/phptop.ini etc/php5/conf.d/
RUN chmod +r /etc/php5/conf.d/phptop.ini

EXPOSE 80

VOLUME /var/www/test/root
CMD apachectl -d /etc/apache2 -f apache2.conf -e info -DFOREGROUND
