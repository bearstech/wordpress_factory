FROM debian:wheezy

RUN apt-get update
RUN apt-get -y upgrade
RUN echo 'mysql-server-5.5 mysql-server/root_password password mypass' | debconf-set-selections && \
    echo 'mysql-server-5.5 mysql-server/root_password_again password mypass' | debconf-set-selections && \
    apt-get -q install -y mysql-server
RUN sed -i -e"s/^bind-address\s*=\s*127.0.0.1/bind-address = 0.0.0.0/" /etc/mysql/my.cnf
RUN /etc/init.d/mysql start && \
    mysql --password=mypass -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'mypass';"

EXPOSE 3306

CMD chown -R mysql:mysql /var/lib/mysql && mysqld
