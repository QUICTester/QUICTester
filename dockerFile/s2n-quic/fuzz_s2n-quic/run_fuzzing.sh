#!/bin/bash

setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_TEMP -p $LEARNER_PORT_TEMP -t $SERVER_PORT_TEMP $LEARN_LIB --docker -r "$SERVER_PATH interop server -p $SERVER_PORT_TEMP --certificate $SERVER_CERT --private-key $SERVER_KEY $RETRY" > run/learner_${SERVER_NAME}_${INPUT_TEMP}_${LEARNER_PORT_TEMP}.log 2>&1  &
setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_SHORT -p $LEARNER_PORT_SHORT -t $SERVER_PORT_SHORT $LEARN_LIB --docker -r "$SERVER_PATH interop server -p $SERVER_PORT_SHORT --certificate $SERVER_CERT --private-key $SERVER_KEY $RETRY" > run/learner_${SERVER_NAME}_${INPUT_SHORT}_${LEARNER_PORT_SHORT}.log 2>&1  &
setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_LONG -p $LEARNER_PORT_LONG -t $SERVER_PORT_LONG $LEARN_LIB --docker -r "$SERVER_PATH interop server -p $SERVER_PORT_LONG --certificate $SERVER_CERT --private-key $SERVER_KEY $RETRY" > run/learner_${SERVER_NAME}_${INPUT_LONG}_${LEARNER_PORT_LONG}.log 2>&1  &
 
wait
