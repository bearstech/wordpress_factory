FROM golang:1.4-wheezy

RUN go get github.com/mailhog/MailHog

EXPOSE 25 8025

ENTRYPOINT ["/go/bin/MailHog", "-smtp-bind-addr", "0.0.0.0:25"]
