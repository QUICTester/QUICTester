#!/bin/bash

export LD_LIBRARY_PATH="$(dirname "$(find /tmp -name libssl3.so -print -quit)")"
ulimit -s 16384

setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_TEMP -p $LEARNER_PORT_TEMP -t $SERVER_PORT_TEMP $LEARN_LIB --docker -r "$SERVER_PATH [::]:$SERVER_PORT_TEMP --db $DB -k cert $RETRY" > run/learner_${SERVER_NAME}_${INPUT_TEMP}_${LEARNER_PORT_TEMP}.log 2>&1 &
setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_SHORT -p $LEARNER_PORT_SHORT -t $SERVER_PORT_SHORT $LEARN_LIB --docker -r "$SERVER_PATH [::]:$SERVER_PORT_SHORT --db $DB -k cert $RETRY" > run/learner_${SERVER_NAME}_${INPUT_SHORT}_${LEARNER_PORT_SHORT}.log 2>&1 &
setsid python3 learner.py -s $SERVER_NAME --config $CONFIG -i $INPUT_LONG -p $LEARNER_PORT_LONG -t $SERVER_PORT_LONG $LEARN_LIB --docker -r "$SERVER_PATH [::]:$SERVER_PORT_LONG --db $DB -k cert $RETRY" > run/learner_${SERVER_NAME}_${INPUT_LONG}_${LEARNER_PORT_LONG}.log 2>&1 &

wait