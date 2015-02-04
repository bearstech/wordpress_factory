FROM debian:wheezy

RUN apt-get update && apt-get -y install bzip2 git openjdk-7-jre-headless curl

WORKDIR /tmp
ENV NODE_VERSION 0.10.35
RUN curl http://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-x64.tar.gz | tar -xvz
RUN mv node-v$NODE_VERSION-linux-x64 /opt/node
RUN ln -s /opt/node/bin/* /usr/local/bin/

WORKDIR /root
RUN npm install -g sitespeed.io
