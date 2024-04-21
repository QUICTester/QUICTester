#!/bin/bash

ulimit -s 16384

# setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_TEMP -p $LEARNER_PORT_TEMP -t $SERVER_PORT_TEMP --caCert ../secrets/serverCert/xquic.crt $LEARN_LIB --docker -r "$SERVER_PATH -p $SERVER_PORT_TEMP" > run/learner_${SERVER_NAME}_${INPUT_TEMP}_${LEARNER_PORT_TEMP}.log 2>&1  &
setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_SHORT -p $LEARNER_PORT_SHORT -t $SERVER_PORT_SHORT --caCert ../secrets/serverCert/xquic.crt $LEARN_LIB --docker -r "$SERVER_PATH -p $SERVER_PORT_SHORT" > run/learner_${SERVER_NAME}_${INPUT_SHORT}_${LEARNER_PORT_SHORT}.log 2>&1  &
# setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_LONG -p $LEARNER_PORT_LONG -t $SERVER_PORT_LONG --caCert ../secrets/serverCert/xquic.crt $LEARN_LIB --docker -r "$SERVER_PATH -p $SERVER_PORT_LONG" > run/learner_${SERVER_NAME}_${INPUT_LONG}_${LEARNER_PORT_LONG}.log 2>&1  &

wait