FROM debian:wheezy

RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y install bzip2 git openjdk-7-jre-headless

ADD http://nodejs.org/dist/v0.10.35/node-v0.10.35-linux-x64.tar.gz /tmp/
WORKDIR /tmp
RUN tar -xvzf node-v0.10.35-linux-x64.tar.gz
RUN mv node-v0.10.35-linux-x64 /opt/node
RUN ln -s /opt/node/bin/* /usr/local/bin/
RUN npm install -g sitespeed.io

