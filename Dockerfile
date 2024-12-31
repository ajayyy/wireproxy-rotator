# Start by building the application.
FROM docker.io/golang:1.21 AS build

WORKDIR /usr/src/wireproxy
COPY . .

RUN make

# Now copy it into our base image.
FROM alpine
COPY --from=build /usr/src/wireproxy/wireproxy /usr/bin/wireproxy

ENV CONFIG_LOCATION="./config.conf"
ENV RELAY_FILE_LOCATION="./relay_list.json"
ENV TIMEOUT="5m"

WORKDIR /usr/src/app
COPY ./controller /usr/src/app/

RUN apk add --no-cache python3 py3-pip cargo
RUN pip3 install --break-system-packages -r /usr/src/app/requirements.txt

# Force unbuffered output to stdout
ENV PYTHONUNBUFFERED=1 

ENTRYPOINT [ "python3" ]
CMD [ "/usr/src/app/app.py" ]

LABEL org.opencontainers.image.title="wireproxy with rotation"
LABEL org.opencontainers.image.description="Wireguard client that exposes itself as a socks5 proxy"
LABEL org.opencontainers.image.licenses="ISC"
