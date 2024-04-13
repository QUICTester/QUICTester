#!/bin/bash

setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_TEMP -p $LEARNER_PORT_TEMP -t $SERVER_PORT_TEMP $LEARN_LIB --docker -r "$SERVER_PATH -listen:127.0.0.1 -name:localhost -port:$SERVER_PORT_TEMP -root:/tmp -file:$SERVER_CERT -key:$SERVER_KEY $RETRY -noexit" > run/learner_${SERVER_NAME}_${INPUT_TEMP}_${LEARNER_PORT_TEMP}.log 2>&1 &
setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_SHORT -p $LEARNER_PORT_SHORT -t $SERVER_PORT_SHORT $LEARN_LIB --docker -r "$SERVER_PATH -listen:127.0.0.1 -name:localhost -port:$SERVER_PORT_SHORT -root:/tmp -file:$SERVER_CERT -key:$SERVER_KEY $RETRY -noexit" > run/learner_${SERVER_NAME}_${INPUT_SHORT}_${LEARNER_PORT_SHORT}.log 2>&1 &
setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_LONG -p $LEARNER_PORT_LONG -t $SERVER_PORT_LONG $LEARN_LIB --docker -r "$SERVER_PATH -listen:127.0.0.1 -name:localhost -port:$SERVER_PORT_LONG -root:/tmp -file:$SERVER_CERT -key:$SERVER_KEY $RETRY -noexit" > run/learner_${SERVER_NAME}_${INPUT_LONG}_${LEARNER_PORT_LONG}.log 2>&1 &

wait