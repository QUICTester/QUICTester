#!/bin/bash

# 
# differential testing for the learned models (same config, same dictionary, same timeout but different server)

# Usage:
# ./compareModel.sh

# before you want to compare the results, categorise the results into 3 different directories in the ../results/*Models/
# CS-short for short timeout results
# CS-long for long timeout results
# CS-temp for mixed (short and long) timeout results

# path that store all the models (edit this if you have different path/config)
MODEL_PATH="../results/*Models"
SHORT_DIR_NAME="CS-short"
LONG_DIR_NAME="CS-long"
TEMP_DIR_NAME="CS-temporal"

# reference models
REF_MODEL_B="../results/ngtcp2Models/CS-temporal/ngtcp2-B-0/optimisedLearnedModel.dot"
REF_MODEL_B_1="../results/quiclyModels/CS-temporal/quicly-B-0/optimisedLearnedModel.dot"
REF_MODEL_B_2="../results/google-quicheModels/CS-temporal/google-quiche-B-B-0/optimisedLearnedModel.dot"

REF_MODEL_BWR="../results/ngtcp2Models/CS-temporal/ngtcp2-BWR-0/optimisedLearnedModel.dot"
REF_MODEL_BWR_1="../results/quiclyModels/CS-temporal/quicly-BWR-0/optimisedLearnedModel.dot"

REF_MODEL_BWCA="../results/ngtcp2Models/CS-temporal/ngtcp2-BWCA-0/optimisedLearnedModel.dot"
REF_MODEL_BWCA_1="../results/google-quicheModels/CS-temporal/google-quiche-BWCA-BWCA-0/optimisedLearnedModel.dot"

REF_MODEL_BWRCA="../results/ngtcp2Models/CS-temporal/ngtcp2-BWRCA-0/optimisedLearnedModel.dot"

REF_MODEL_PSK="../results/ngtcp2Models/CS-temporal/ngtcp2-PSK-0/optimisedLearnedModel.dot"
REF_MODEL_PSK_1="../results/quiclyModels/CS-temporal/quicly-PSK-0/optimisedLearnedModel.dot"
REF_MODEL_PSK_2="../results/google-quicheModels/CS-temporal/google-quiche-PSK-PSK-0/optimisedLearnedModel.dot"

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

# fucntion that do the comparision
compare(){
    sutName=$(basename "$1")
    sutName=${sutName/"Models"/""}

    for shortDir in "$1/$SHORT_DIR_NAME"/* "$1/$LONG_DIR_NAME"/* "$1/$TEMP_DIR_NAME"/* ; do
        isCheckModel=0
        
        # script to change dir name here
        # newDirPath=""
        # if [ -d "$shortDir" ]; then
        #     if [[ "$shortDir" == *"/$LONG_DIR_NAME/"* ]]; then
        #         newDirPath="${shortDir/-lCS-/-l-}"
        #     elif [[ "$shortDir" == *"/$TEMP_DIR_NAME/"* ]];then
        #         newDirPath="${shortDir/-CS-/-}"
        #     elif [[ "$shortDir" == *"/$SHORT_DIR_NAME/"* ]]; then
        #         newDirPath="${shortDir/-sCS-/-s-}"
        #     fi

        #     if [[ ! -z "$newDirPath" ]]; then
        #         mv $shortDir $newDirPath
        #     fi
        # fi
        
        # compare the unique models
        if [ -d "$shortDir" ]; then
            # remove old results (if any)
            if [ -e "$shortDir/refModelCompare.dot" ]; then
                rm "$shortDir/refModelCompare.dot"
            fi
            
            # count how many models are there
            if [ -e "$shortDir/$OPT_DOT_FILE" ]; then
                ((totalCount++))
            fi

            # if the model is with long timeout, check the model if it is not same as the model with short timeout
            if [[ "$shortDir" == *"/$LONG_DIR_NAME/"* ]] && [ -e "$shortDir/$SHORT_LONG_COMPARE" ]; then
                isCheckModel=1

            # if the model is with mixed timeout, check the model if it is not same as the model with long timeout
            elif [[ "$shortDir" == *"/$TEMP_DIR_NAME/"* ]] && [ -e "$shortDir/$LONG_TEMP_COMPARE" ];then
                isCheckModel=1

            # always check the model with short timeout
            elif [[ "$shortDir" == *"/$SHORT_DIR_NAME/"* ]]; then
                isCheckModel=1
            fi

            if [ $isCheckModel -eq 1 ]; then
                dirBasename=$(basename "$shortDir")
                shortFile=$shortDir/$OPT_DOT_FILE
                refModel=""
                refModel1=""
                refModel2=""
                
                # choose which model configuration to compare
                if [[ "$dirBasename" == "$sutName-$B-"* ]]; then
                    refModel=$REF_MODEL_B
                    refModel1=$REF_MODEL_B_1
                    refModel2=$REF_MODEL_B_2
                elif [[ "$dirBasename" == "$sutName-$BWR-"* ]]; then
                    refModel=$REF_MODEL_BWR
                    refModel1=$REF_MODEL_BWR_1
                elif [[ "$dirBasename" == "$sutName-$BWCA-"* ]]; then
                    refModel=$REF_MODEL_BWCA
                    refModel1=$REF_MODEL_BWCA_1
                    #refModel2=$REF_MODEL_BWCA_2
                elif [[ "$dirBasename" == "$sutName-$BWRCA-"* ]]; then
                    refModel=$REF_MODEL_BWRCA
                    #refModel1=$REF_MODEL_BWRCA_1
                    #refModel2=$REF_MODEL_BWRCA_2
                elif [[ "$dirBasename" == "$sutName-$PSK-"* ]]; then
                    refModel=$REF_MODEL_PSK
                    refModel1=$REF_MODEL_PSK_1
                    refModel2=$REF_MODEL_PSK_2
                fi

                # remove server response from the dot file
                if [ -e "$refModel" ]; then
                    sed 's/\/.*"/ "/g' "$refModel" > $TEMP_REF_FILE
                fi

                # remove server response from the dot file
                if [ -e "$refModel1" ]; then
                    sed 's/\/.*"/ "/g' "$refModel1" > $TEMP_REF_FILE_1
                fi

                # remove server response from the dot file
                if [ -e "$refModel2" ]; then
                    sed 's/\/.*"/ "/g' "$refModel2" > $TEMP_REF_FILE_2
                fi

                # remove _short/_long from the dot file
                if [ -e "$shortFile" ]; then
                    sed "s/$SHORT_INPUT_SYMBOL/$TEMPORAL_INPUT_SYMBOL/g" "$shortFile" > $TEMP_CMP_FILE
                    sed -i "s/$LONG_INPUT_SYMBOL/$TEMPORAL_INPUT_SYMBOL/g" "$TEMP_CMP_FILE"
                    #sed -i "s/,NewToken//g" "$TEMP_CMP_FILE"
                    sed -i 's/\/.*"/ "/g' "$TEMP_CMP_FILE"
                fi

                # compare short and long
                if [ -e "$refModel" ] && [ -e "$shortFile" ]; then
                    python3 $LTS_DIFF --ref=$TEMP_REF_FILE --upd=$TEMP_CMP_FILE -s cvc4 -o $TEMP_RESULT_FILE
                    
                    # check if there is reduced(red)/added(green) edges in the result file
                    if grep -q "color=red" $TEMP_RESULT_FILE || grep -q "color=green" $TEMP_RESULT_FILE; then

                        # check the second ref model
                        if [ -e "$refModel1" ]; then
                            python3 $LTS_DIFF --ref=$TEMP_REF_FILE_1 --upd=$TEMP_CMP_FILE -s cvc4 -o $TEMP_RESULT_FILE_1

                            if grep -q "color=red" $TEMP_RESULT_FILE_1 || grep -q "color=green" $TEMP_RESULT_FILE_1; then

                                # check the third ref model
                                if [ -e "$refModel2" ]; then
                                    python3 $LTS_DIFF --ref=$TEMP_REF_FILE_2 --upd=$TEMP_CMP_FILE -s cvc4 -o $TEMP_RESULT_FILE_2

                                    if grep -q "color=red" $TEMP_RESULT_FILE_2 || grep -q "color=green" $TEMP_RESULT_FILE_2; then
                                        cp $TEMP_RESULT_FILE $shortDir/refModelCompare.dot
                                        echo "  $shortDir and reference model are different."
                                        ((diffCount++))
                                    fi
                                else    
                                    cp $TEMP_RESULT_FILE $shortDir/refModelCompare.dot
                                    echo "  $shortDir and reference model are different."
                                    ((diffCount++))
                                fi
                            fi
                        else    
                            cp $TEMP_RESULT_FILE $shortDir/refModelCompare.dot
                            echo "  $shortDir and reference model are different."
                            ((diffCount++))
                        fi
                        
                    fi
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

echo "Total Count: $totalCount"
echo "Diff Count: $diffCount"

rm $TEMP_CMP_FILE $TEMP_RESULT_FILE $TEMP_REF_FILE $TEMP_RESULT_FILE_1 $TEMP_REF_FILE_1 $TEMP_RESULT_FILE_2 $TEMP_REF_FILE_2

#temporary way to compare 2 dot file (only compare the states)
#dot -Tplain aioModels/CS-temporal/aio-B-CS-0/optimisedLearnedModel.dot | sed -ne 's/^node \([^ ]\+\).*$/\1/p' | sort >a1.nodes
#dot -Tplain aioModels/CS-temporal/aio-B-CS-0/optimisedLearnedModel.dot | sed -ne 's/^node \([^ ]\+\).*$/\1/p' | sort >a2.nodes
#diff a1.nodes a2.nodes
