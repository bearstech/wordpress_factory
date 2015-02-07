FROM debian:wheezy

RUN apt-get update && apt-get install -y memcached sasl2-bin && rm -rf /var/lib/apt/lists/*

RUN groupadd -r memcache && useradd -r -g memcache -G sasl memcache

COPY docker-entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 11211
CMD ["sh", "/start-memcached"]
