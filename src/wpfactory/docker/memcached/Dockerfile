FROM debian:wheezy

RUN apt-get update && apt-get install -y memcached sasl2-bin && rm -rf /var/lib/apt/lists/*

COPY docker-entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 11211
CMD ["sh", "/start-memcached"]
