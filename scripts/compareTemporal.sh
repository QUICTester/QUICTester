#!/bin/bash

# 
# differential testing for the learned models (same config, same dictionary but different timeout)

# Usage:
# ./compareTemporal.sh

# before you want to compare the results, categorise the results into 3 different directories in the ../results/*Models
# CS-short for short timeout results
# CS-long for long timeout results
# CS-temp for mixed (short and long) timeout results

# path that store all the models (edit this if you have different path/config)
MODEL_PATH="../results/*Models"
SHORT_DIR_NAME="CS-short"
LONG_DIR_NAME="CS-long"
TEMP_DIR_NAME="CS-temporal"

# config/dictionary symbols in the results dir name
B="B"
BWR="BWR"
BWCA="BWCA"
BWRCA="BWRCA"
PSK="PSK"

# # extra dictionary symbols
# SHORT_SYMBOL="-sCS-"
# LONG_SYMBOL="-lCS-"
# TEMP_SYMBOL="-CS-"

# NEW dictionary symbols
SHORT_SYMBOL="-s-"
LONG_SYMBOL="-l-"
TEMP_SYMBOL="-"

# input symbols
LONG_INPUT_SYMBOL="_long"
SHORT_INPUT_SYMBOL="_short"
TEMPORAL_INPUT_SYMBOL=""

# file to compare
OPT_DOT_FILE="optimisedLearnedModel.dot"

# some constant name for temporary file
TEMP_SHORT_FILE="tempShortFile.dot"
TEMP_LONG_FILE="tempLongFile.dot"
TEMP_RESULT_FILE="tempResult.dot"

# LTS Diff program
LTS_DIFF="ltsDiff/algorithm/main.py"

# fucntion that do the comparision
compare(){
    for shortDir in $1/$SHORT_DIR_NAME/*; do
        if [ -d "$shortDir" ]; then
            # get the results with the short timeout to compare
            shortFile=$shortDir/$OPT_DOT_FILE
            #echo $shortFile
            
            # get the results with the long timeout to compare
            longDir=$(basename "$shortDir")
            longDir="${longDir/$SHORT_SYMBOL/$LONG_SYMBOL}"
            longDir=$1/$LONG_DIR_NAME/$longDir
            longFile=$longDir/$OPT_DOT_FILE

            # get the results with the temporal timeout to compare
            tempDir=$(basename "$shortDir")
            tempDir="${tempDir/$SHORT_SYMBOL/$TEMP_SYMBOL}"
            tempDir=$1/$TEMP_DIR_NAME/$tempDir
            temporalFile=$tempDir/$OPT_DOT_FILE

            # remove _short from the dot file
            if [ -e "$shortFile" ]; then
                sed "s/$SHORT_INPUT_SYMBOL/$TEMPORAL_INPUT_SYMBOL/g" "$shortFile" > $TEMP_SHORT_FILE
            fi
            
            # remove _long from the dot file
            if [ -e "$longFile" ]; then
                sed "s/$LONG_INPUT_SYMBOL/$TEMPORAL_INPUT_SYMBOL/g" "$longFile" > $TEMP_LONG_FILE
            fi

            # compare short and long
            if [ -e "$shortFile" ] && [ -e "$longFile" ]; then
                python3 $LTS_DIFF --ref=$TEMP_SHORT_FILE --upd=$TEMP_LONG_FILE -s cvc4 -o $TEMP_RESULT_FILE
                
                # check if there is reduced(red)/added(green) edges in the result file
                if grep -q "color=red" $TEMP_RESULT_FILE || grep -q "color=green" $TEMP_RESULT_FILE; then
                    cp $TEMP_RESULT_FILE $shortDir/shortLongCompare.dot
                    cp $TEMP_RESULT_FILE $longDir/shortLongCompare.dot
                    echo "  $shortDir and $longDir are different."
                fi 
            fi

            # compare short and temporal
            if [ -e "$shortFile" ] && [ -e "$temporalFile" ]; then
                python3 $LTS_DIFF --ref=$TEMP_SHORT_FILE --upd=$temporalFile -s cvc4 -o $TEMP_RESULT_FILE
                
                # check if there is reduced(red)/added(green) edges in the result file
                if grep -q "color=red" $TEMP_RESULT_FILE || grep -q "color=green" $TEMP_RESULT_FILE; then
                    cp $TEMP_RESULT_FILE $shortDir/shortTempCompare.dot
                    cp $TEMP_RESULT_FILE $tempDir/shortTempCompare.dot
                    echo "  $shortDir and $tempDir are different."
                fi 
            fi

            # compare temporal and long
            if [ -e "$temporalFile" ] && [ -e "$longFile" ]; then
                python3 $LTS_DIFF --ref=$TEMP_LONG_FILE --upd=$temporalFile -s cvc4 -o $TEMP_RESULT_FILE
                
                # check if there is reduced(red)/added(green) edges in the result file
                if grep -q "color=red" $TEMP_RESULT_FILE || grep -q "color=green" $TEMP_RESULT_FILE; then
                    cp $TEMP_RESULT_FILE $longDir/longTempCompare.dot
                    cp $TEMP_RESULT_FILE $tempDir/longTempCompare.dot
                    echo "  $longDir and $tempDir are different."
                fi 
            fi

        fi
    done
}

for dir in $MODEL_PATH; do
    if [ -d "$dir" ]; then
        # check the short timeout dir first
        #echo $(basename $dir)
        compare $dir
        echo ""
    fi    
done

rm $TEMP_SHORT_FILE $TEMP_LONG_FILE $TEMP_RESULT_FILE

#temporary way to compare 2 dot file (only compare the states)
#dot -Tplain aioModels/CS-temporal/aio-B-CS-0/optimisedLearnedModel.dot | sed -ne 's/^node \([^ ]\+\).*$/\1/p' | sort >a1.nodes
#dot -Tplain aioModels/CS-temporal/aio-B-CS-0/optimisedLearnedModel.dot | sed -ne 's/^node \([^ ]\+\).*$/\1/p' | sort >a2.nodes
#diff a1.nodes a2.nodes

# another way is to compare all the models with the one that is correct (quinn maybe?)
