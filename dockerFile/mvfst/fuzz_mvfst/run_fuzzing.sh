#!/bin/bash

ulimit -s 16384

setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_TEMP -p $LEARNER_PORT_TEMP -t $SERVER_PORT_TEMP -c $CLIENT_CERT -k $CLIENT_KEY $LEARN_LIB --docker -r "$SERVER_PATH/hq -port=$SERVER_PORT_TEMP -h2port=$H2_SERVER_PORT_TEMP -mode=server -host=0.0.0.0 -key=$SERVER_KEY -cert=$SERVER_CERT -protocol=hq-interop -connect_udp=true -threads=2 -client_auth_mode=$CLIENT_AUTH" > run/learner_${SERVER_NAME}_${INPUT_TEMP}_${LEARNER_PORT_TEMP}.log 2>&1 &
setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_SHORT -p $LEARNER_PORT_SHORT -t $SERVER_PORT_SHORT -c $CLIENT_CERT -k $CLIENT_KEY $LEARN_LIB --docker -r "$SERVER_PATH/hq -port=$SERVER_PORT_SHORT -h2port=$H2_SERVER_PORT_SHORT -mode=server -host=0.0.0.0 -key=$SERVER_KEY -cert=$SERVER_CERT -protocol=hq-interop -connect_udp=true -threads=2 -client_auth_mode=$CLIENT_AUTH" > run/learner_${SERVER_NAME}_${INPUT_SHORT}_${LEARNER_PORT_SHORT}.log 2>&1 &
setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_LONG -p $LEARNER_PORT_LONG -t $SERVER_PORT_LONG -c $CLIENT_CERT -k $CLIENT_KEY $LEARN_LIB --docker -r "$SERVER_PATH/hq -port=$SERVER_PORT_LONG -h2port=$H2_SERVER_PORT_LONG -mode=server -host=0.0.0.0 -key=$SERVER_KEY -cert=$SERVER_CERT -protocol=hq-interop -connect_udp=true -threads=2 -client_auth_mode=$CLIENT_AUTH" > run/learner_${SERVER_NAME}_${INPUT_LONG}_${LEARNER_PORT_LONG}.log 2>&1 &

wait