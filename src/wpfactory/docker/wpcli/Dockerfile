FROM debian:wheezy

# Base system
RUN apt-get update && apt-get -y install \
    php5-mysql php-apc \
    php5-memcached php5-curl php5-gd php5-intl php-pear php5-imagick adduser\
    php5-imap php5-mcrypt php5-cli less wget mysql-client curl python git ssmtp \
    && rm -r /var/lib/apt/lists/*

RUN wget https://github.com/wp-cli/wp-cli/releases/download/v0.18.0/wp-cli-0.18.0.phar -O /usr/local/bin/wp
RUN chmod +x /usr/local/bin/wp
#RUN mkdir -p /root/.wp-cli/
ADD wp-cli.yml /etc/wp-cli.yml
#ENV WP_CLI_CONFIG_PATH /etc/wp-cli.yml

WORKDIR /opt/
RUN git clone https://github.com/danielbachhuber/dictator.git

VOLUME /var/www/test/root

CMD wp help
