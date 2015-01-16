FROM debian:wheezy

RUN apt-get update
RUN apt-get -y upgrade
RUN echo "deb http://ftp.debian.org/debian/ wheezy-backports main" > /etc/apt/sources.list.d/backport.list
RUN apt-get update
RUN apt-get -y install haproxy
