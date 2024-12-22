#!/bin/sh

# Clean up background process on exit
cleanup() {
    kill $wireproxy_pid
    exit 0
}

trap cleanup SIGINT

while :
do
python3 create-config.py

timeout $TIMEOUT /usr/bin/wireproxy --config ./config.conf &
wireproxy_pid=$!

# Wait for either a timeout or the termination of the process
wait $wireproxy_pid
done