FROM debian:wheezy

RUN apt-get update && apt-get -y install bzip2 git openjdk-7-jre-headless curl

WORKDIR /tmp

ENV NODE_VERSION 0.10.35
RUN mkdir -p /opt/node \
        && curl -L "http://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-x64.tar.gz" \
        | tar -xvzC /opt/node --strip-components=1 \
        && ln -s /opt/node/bin/* /usr/local/bin/

WORKDIR /root
RUN npm install -g sitespeed.io
