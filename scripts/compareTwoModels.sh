#!/bin/bash

# 
# compare 2 models
# Usage:
# ./compareTwoModels.sh /path/to/model/one /path/to/model/two


# config/dictionary symbols in the results dir name
B="B"
BWR="BWR"
BWCA="BWCA"
BWRCA="BWRCA"

# extra dictionary symbols
SHORT_SYMBOL="-sCS-"
LONG_SYMBOL="-lCS-"
TEMP_SYMBOL="-CS-"

# input symbols
LONG_INPUT_SYMBOL="_long"
SHORT_INPUT_SYMBOL="_short"
TEMPORAL_INPUT_SYMBOL=""

# some constant name for temporary file
TEMP_REF_FILE="tempRefFile.dot"
TEMP_CMP_FILE="tempCmpFile.dot"
TEMP_RESULT_FILE="tempResult.dot"

# LTS Diff program
LTS_DIFF="ltsDiff/algorithm/main.py"

# fucntion that do the comparision
compare(){
    model1=$1
    model2=$2

    # remove _short/_long from the dot files
    if [ -e "$model1" ]; then
        sed "s/$SHORT_INPUT_SYMBOL/$TEMPORAL_INPUT_SYMBOL/g" "$model1" > $TEMP_REF_FILE
        sed -i "s/$LONG_INPUT_SYMBOL/$TEMPORAL_INPUT_SYMBOL/g" "$TEMP_REF_FILE"
        sed -i 's/\/.*"/ "/g' "$TEMP_REF_FILE"
    fi

    if [ -e "$model2" ]; then
        sed "s/$SHORT_INPUT_SYMBOL/$TEMPORAL_INPUT_SYMBOL/g" "$model2" > $TEMP_CMP_FILE
        sed -i "s/$LONG_INPUT_SYMBOL/$TEMPORAL_INPUT_SYMBOL/g" "$TEMP_CMP_FILE"
        sed -i 's/\/.*"/ "/g' "$TEMP_CMP_FILE"
    fi

    # compare short and long
    if [ -e "$model1" ] && [ -e "$model2" ]; then       
        python3 $LTS_DIFF --ref=$TEMP_REF_FILE --upd=$TEMP_CMP_FILE -s cvc4 -o $TEMP_RESULT_FILE
                
        # check if there is reduced(red)/added(green) edges in the result file
        if grep -q "color=red" $TEMP_RESULT_FILE || grep -q "color=green" $TEMP_RESULT_FILE; then
            echo "  The models are different."
        else
            echo "  The models are same."
        fi
    fi
}

rm $TEMP_RESULT_FILE 2> /dev/null

compare $1 $2

rm $TEMP_CMP_FILE $TEMP_REF_FILE

#temporary way to compare 2 dot file (only compare the states)
#dot -Tplain aioModels/CS-temporal/aio-B-CS-0/optimisedLearnedModel.dot | sed -ne 's/^node \([^ ]\+\).*$/\1/p' | sort >a1.nodes
#dot -Tplain aioModels/CS-temporal/aio-B-CS-0/optimisedLearnedModel.dot | sed -ne 's/^node \([^ ]\+\).*$/\1/p' | sort >a2.nodes
#diff a1.nodes a2.nodes

# another way is to compare all the models with the one that is correct (quinn maybe?)
