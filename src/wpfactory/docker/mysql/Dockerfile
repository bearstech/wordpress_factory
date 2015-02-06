FROM debian:wheezy

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -q install -y --no-install-recommends mysql-server mysql-client && \
    rm -r /var/lib/apt/lists/* /var/lib/mysql/*

RUN sed -i -e"s/^bind-address/#bind-address/" /etc/mysql/my.cnf

VOLUME /var/lib/mysql

COPY docker-entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 3306

CMD ["mysqld"]
