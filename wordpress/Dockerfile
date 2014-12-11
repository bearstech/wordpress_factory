FROM debian:wheezy

RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y install php5-cgi php5-mysql apache2-mpm-worker apache2-suexec libapache2-mod-fcgid
RUN mkdir -p /var/log/apache2/test.example.com
ADD website.conf /etc/apache2/sites-available/
RUN ln -s /etc/apache2/sites-available/website.conf /etc/apache2/sites-enabled/
ADD fcgid.conf /etc/apache2/mods-available/

EXPOSE 80

VOLUME /var/www/test/root
CMD apachectl -d /etc/apache2 -f apache2.conf -e info -DFOREGROUND
