#!/bin/bash

# author: Kian Kai Ang
# differential testing for the learned models (same config, same dictionary, same timeout but different server)

# Usage:
# ./compareModel.sh

# before you want to compare the results, categorise the results into 3 different directories in the ../results/*Models/
# CS-short for short timeout results
# CS-long for long timeout results
# CS-temp for mixed (short and long) timeout results

# path that store all the models (edit this if you have different path/config)
# MODEL_PATH="../results/*Models"
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

# for PSK
# SHORT_SYMBOL="-s-"
# LONG_SYMBOL="-l-"
# TEMP_SYMBOL=""

# input symbols
LONG_INPUT_SYMBOL="_long"
SHORT_INPUT_SYMBOL="_short"
TEMPORAL_INPUT_SYMBOL=""

# file to compare
OPT_DOT_FILE="optimisedLearnedModel.dot"

# some constant name for temporary file
TEMP_REF_FILE="tempRefFile.dot"
TEMP_REF_FILE_1="tempRefFile1.dot"
TEMP_REF_FILE_2="tempRefFile2.dot"
TEMP_CMP_FILE="tempCmpFile.dot"
TEMP_RESULT_FILE="tempResult.dot"
TEMP_RESULT_FILE_1="tempResult1.dot"
TEMP_RESULT_FILE_2="tempResult2.dot"

# output file name from compareTemporal.sh
SHORT_LONG_COMPARE="shortLongCompare.dot"
SHORT_TEMP_COMPARE="shortTempCompare.dot"
LONG_TEMP_COMPARE="longTempCompare.dot"

# LTS Diff program
LTS_DIFF="ltsDiff/algorithm/main.py"

# keep track how many models are different
diffCount=0
totalCount=0

# fucntion that do the cross-check comparision
compare(){
    sutName=$(basename "$1")
    sutName=${sutName/"Models"/""}
    diffModelsDir="$1/crossCheckResults"
    echo "Analysing $sutName..." 

    # remove old results (if any)
    if [ -d "$diffModelsDir" ]; then
        rm -r $diffModelsDir
    fi

    # make a new dir to store all the diff models
    mkdir $diffModelsDir

    for currentDir in "$1/$SHORT_DIR_NAME"/* "$1/$LONG_DIR_NAME"/* "$1/$TEMP_DIR_NAME"/* ; do
        isCheckModel=0
        
        # compare the unique models
        if [ -d "$currentDir" ]; then
            # count how many models are there
            if [ -e "$currentDir/$OPT_DOT_FILE" ]; then
                ((totalCount++))
            fi

            # if the model is with long timeout, check the model if it is not same as the model with short timeout
            if [[ "$currentDir" == *"/$LONG_DIR_NAME/"* ]] && [ -e "$currentDir/$SHORT_LONG_COMPARE" ]; then
                isCheckModel=1

            # if the model is with mixed timeout, check the model if it is not same as the model with long timeout
            elif [[ "$currentDir" == *"/$TEMP_DIR_NAME/"* ]] && [ -e "$currentDir/$LONG_TEMP_COMPARE" ];then
                isCheckModel=1

            # always check the model with short timeout
            elif [[ "$currentDir" == *"/$SHORT_DIR_NAME/"* ]]; then
                isCheckModel=1
            fi

            if [ $isCheckModel -eq 1 ]; then
                currentDirBasename=$(basename "$currentDir")
                optFile=$currentDir/$OPT_DOT_FILE

                # remove _short/_long from the current dot file 
                if [ -e "$optFile" ]; then
                    sed "s/$SHORT_INPUT_SYMBOL/$TEMPORAL_INPUT_SYMBOL/g" "$optFile" > $TEMP_CMP_FILE
                    sed -i "s/$LONG_INPUT_SYMBOL/$TEMPORAL_INPUT_SYMBOL/g" "$TEMP_CMP_FILE"
                    sed -i 's/\/.*"/ "/g' "$TEMP_CMP_FILE"
                fi
                
                for crossCheckSutDir in $MODEL_PATH; do
                    if [ -d "$crossCheckSutDir" ] && [[ "$crossCheckSutDir" != "$1" ]] ; then
                        crossCheckSUTName=$(basename "$crossCheckSutDir")
                        crossCheckSUTName=${crossCheckSUTName/"Models"/""}
                        # echo $crossCheckSUTName

                        # choose which model configuration to compare
                        if [[ "$currentDirBasename" == "$sutName-$B-"* ]]; then
                            crossCheckModelsSuffix="$crossCheckSUTName-$B-"
                        elif [[ "$currentDirBasename" == "$sutName-$BWR-"* ]]; then
                            crossCheckModelsSuffix="$crossCheckSUTName-$BWR-"
                        elif [[ "$currentDirBasename" == "$sutName-$BWCA-"* ]]; then
                            crossCheckModelsSuffix="$crossCheckSUTName-$BWCA-"
                        elif [[ "$currentDirBasename" == "$sutName-$BWRCA-"* ]]; then
                            crossCheckModelsSuffix="$crossCheckSUTName-$BWRCA-"
                        elif [[ "$currentDirBasename" == "$sutName-$PSK-"* ]]; then
                            crossCheckModelsSuffix="$crossCheckSUTName-$PSK-"
                        fi
                        
                        # only cross-check the first file with the same config
                        for crossCheckModelDir in "$crossCheckSutDir/$SHORT_DIR_NAME/$crossCheckModelsSuffix"*"-0"; do
                            # echo $crossCheckModelDir
                            crossCheckModelBasename=$(basename "$crossCheckModelDir")
                            crossCheckModelOpt=$crossCheckModelDir/$OPT_DOT_FILE

                            # since we use all short model for cross-check, only need to remove _short
                            if [ -e "$crossCheckModelOpt" ]; then
                                sed "s/$SHORT_INPUT_SYMBOL/$TEMPORAL_INPUT_SYMBOL/g" "$crossCheckModelOpt" > $TEMP_REF_FILE
                                sed -i 's/\/.*"/ "/g' "$TEMP_REF_FILE"
                            fi

                             # use ltsDiff to generate diff dot file
                            if [ -e "$crossCheckModelOpt" ] && [ -e "$optFile" ]; then
                                python3 $LTS_DIFF --ref=$TEMP_REF_FILE --upd=$TEMP_CMP_FILE -s cvc4 -o "$diffModelsDir/${currentDirBasename}_vs_${crossCheckModelBasename}.dot"
                                break
                            fi
                        done
                    fi
                done
            fi
        fi
    done

    # call python script to identify all input sequences lead to deviations
    echo "  Extracting all the deviating state transitions to $diffModelsDir/ ..."
    python3 extractDeviations.py -d $diffModelsDir -s $sutName
}

for dir in $MODEL_PATH; do
    if [ -d "$dir" ]; then
        # check the short timeout dir first
        #echo $(basename $dir)
        compare $dir
        echo ""
    fi    
done

echo "Total Count: $totalCount"
echo "Analysis Done."
# echo "Diff Count: $diffCount"

rm $TEMP_CMP_FILE  $TEMP_REF_FILE

#temporary way to compare 2 dot file (only compare the states)
#dot -Tplain aioModels/CS-temporal/aio-B-CS-0/optimisedLearnedModel.dot | sed -ne 's/^node \([^ ]\+\).*$/\1/p' | sort >a1.nodes
#dot -Tplain aioModels/CS-temporal/aio-B-CS-0/optimisedLearnedModel.dot | sed -ne 's/^node \([^ ]\+\).*$/\1/p' | sort >a2.nodes
#diff a1.nodes a2.nodes

# another way is to compare all the models with the one that is correct (quinn maybe?)
