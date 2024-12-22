# Start by building the application.
FROM docker.io/golang:1.21 AS build

WORKDIR /usr/src/wireproxy
COPY . .

RUN make

# Now copy it into our base image.
FROM alpine
COPY --from=build /usr/src/wireproxy/wireproxy /usr/bin/wireproxy

ENV CONFIG_LOCATION="./config.conf"
ENV TIMEOUT="5m"

WORKDIR /usr/src/app
COPY ./scripts /usr/src/app/

RUN apk add python3 py3-requests

ENTRYPOINT [ "/usr/src/app/start.sh" ]

LABEL org.opencontainers.image.title="wireproxy with rotation"
LABEL org.opencontainers.image.description="Wireguard client that exposes itself as a socks5 proxy"
LABEL org.opencontainers.image.licenses="ISC"
