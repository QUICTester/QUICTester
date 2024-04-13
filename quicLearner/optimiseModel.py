# 
# purpose: optimise the learned model, 

from imp import new_module
from aalpy.utils.FileHandler import visualize_automaton, load_automaton_from_file
import argparse
import sys

sys.path.insert(0, "../quicMapper/")
from inOutPut import Output, Input

# remove state transitions that cannot lead to a new state.
# optimise function before S&P'24
def optimiseDotFileOld(dotFile):
    with open(dotFile, "r") as file:
        dot = file.readlines()
    
    optimisedDot = ""

    # only take those state transitions that move on to a new state 
    # merge state transitions that does not move on to the new state into one
    for line in dot:
        if ("->" in line and not "label=\"\"" in line):
            data = line.split()

            # transition to new state, ignore if self-loop
            if(data[0] != data[2]):
                previousState = data[0]
                nextState = data[2]
                input = data[3].split('/')[0].split('"')[1]
                inputType = input.split('_')[0]
                output = data[3].split('/')[1]
                isMerge = False
                
                # ignore if the invalid input lead to a connectionClose
                if(not ((inputType == Input.HANDSHAKE_EMPTY_CERTIFICATE or inputType == Input.HANDSHAKE_INVALID_CERTIFICATE or 
                    inputType == Input.INVALID_NEW_CONNECTION_ID) and output == Output.NORMAL_CONNECTION_CLOSE)):
                    for line2 in dot:
                        if ("->" in line2 and not "label=\"\"" in line2):
                            data2 = line2.split()
                            previousState2 = data2[0]
                            nextState2 = data2[2]
                            input2 = data2[3].split('/')[0].split('"')[1]
                            inputType2 = input2.split('_')[0]
                            output2 = data2[3].split('/')[1]

                            # same previous and next states; same inputType (Except Initial Client Hello)
                            if(previousState == previousState2 and nextState == nextState2 and inputType == inputType2 and 
                                input != input2 and output == output2):
                                isMerge = True
                                #print(line)
                                
                                # remove "_short" or "_long" 
                                newLine = line.split('_')[0] + "/" + line.split('/')[1]
                                
                                # add the modify line to the list if it does not exists.
                                if(newLine not in optimisedDot):
                                    optimisedDot += newLine
                                    #print(newLine)

                                break                
                    if(not isMerge):
                        optimisedDot += line
                #optimisedDot += line
        else:
            optimisedDot += line

    # merge initial Client Hello wth different cipher suite here
    lines = optimisedDot.splitlines()
    optimisedDot = ""

    for line in lines:
        if ("->" in line and not "label=\"\"" in line):
            data = line.split()
            previousState = data[0]
            nextState = data[2]
            input = data[3].split('/')[0].split('"')[1]
            output = data[3].split('/')[1]
            
            # merge initialClientHello-validACK
            if(Input.INITIAL_CLIENT_HELLO_VALID_ACK in line):
                allSame = 1

                for line2 in lines:
                    if ("->" in line2 and not "label=\"\"" in line2):
                        data2 = line2.split()
                        previousState2 = data2[0]
                        nextState2 = data2[2]
                        input2 = data2[3].split('/')[0].split('"')[1]
                        output2 = data2[3].split('/')[1]

                        # if 3 of the ciphger suite lead to same nextState from same previousState and have same output, merge them
                        if(Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_128_GCM_SHA256 in input):
                            if(Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_256_GCM_SHA384 in input2 or Input.INITIAL_CLIENT_HELLO_VALID_ACK_CHACHA20_POLY1305_SHA256 in input2):
                                if(previousState == previousState2 and nextState == nextState2 and 
                                        input != input2 and output == output2):
                                    allSame += 1
                        elif(Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_256_GCM_SHA384 in input):
                            if(Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_128_GCM_SHA256 in input2 or Input.INITIAL_CLIENT_HELLO_VALID_ACK_CHACHA20_POLY1305_SHA256 in input2):
                                if(previousState == previousState2 and nextState == nextState2 and 
                                        input != input2 and output == output2):
                                    allSame += 1
                        elif(Input.INITIAL_CLIENT_HELLO_VALID_ACK_CHACHA20_POLY1305_SHA256 in input):
                            if(Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_128_GCM_SHA256 in input2 or Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_256_GCM_SHA384 in input2):
                                if(previousState == previousState2 and nextState == nextState2 and 
                                        input != input2 and output == output2):
                                    allSame += 1
                        
                        if(allSame == 3):
                            break
                
                # there is at most 3 cipher suites so make sure it does not exceed 3
                assert(allSame < 4)
                
                # merge them, if they has short or long symbol, keep it
                if(allSame == 3):
                    if(Input.SHORT_SYMBOL in line):
                        newLine = line.split(':')[0] + Input.SHORT_SYMBOL + "/" + line.split('/')[1] + "\n"
                    elif(Input.LONG_SYMBOL in line):
                        newLine = line.split(':')[0] + Input.LONG_SYMBOL + "/" + line.split('/')[1] + "\n"
                    else:
                        newLine = line.split(':')[0] + "/" + line.split('/')[1] + "\n"

                    if(newLine not in optimisedDot):
                        optimisedDot += newLine
                else:
                    optimisedDot = optimisedDot + line + "\n"

            # merge initialClientHello-invalidACK
            elif(Input.INITIAL_CLIENT_HELLO_INVALID_ACK in line):
                allSame = 1

                for line2 in lines:
                    if ("->" in line2 and not "label=\"\"" in line2):
                        data2 = line2.split()
                        previousState2 = data2[0]
                        nextState2 = data2[2]
                        input2 = data2[3].split('/')[0].split('"')[1]
                        output2 = data2[3].split('/')[1]

                        # if 3 of the ciphger suite lead to same nextState from same previousState and have same output, merge them
                        if(Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_128_GCM_SHA256 in input):
                            if(Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_256_GCM_SHA384 in input2 or Input.INITIAL_CLIENT_HELLO_INVALID_ACK_CHACHA20_POLY1305_SHA256 in input2):
                                if(previousState == previousState2 and nextState == nextState2 and 
                                        input != input2 and output == output2):
                                    allSame += 1
                        elif(Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_256_GCM_SHA384 in input):
                            if(Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_128_GCM_SHA256 in input2 or Input.INITIAL_CLIENT_HELLO_INVALID_ACK_CHACHA20_POLY1305_SHA256 in input2):
                                if(previousState == previousState2 and nextState == nextState2 and 
                                        input != input2 and output == output2):
                                    allSame += 1
                        elif(Input.INITIAL_CLIENT_HELLO_INVALID_ACK_CHACHA20_POLY1305_SHA256 in input):
                            if(Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_128_GCM_SHA256 in input2 or Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_256_GCM_SHA384 in input2):
                                if(previousState == previousState2 and nextState == nextState2 and 
                                        input != input2 and output == output2):
                                    allSame += 1
                        
                        if(allSame == 3):
                            break
                
                # there is at most 3 cipher suites so make sure it does not exceed 3
                assert(allSame < 4)
                
                # merge them, if they has short or long symbol, keep it
                if(allSame == 3):
                    if(Input.SHORT_SYMBOL in line):
                        newLine = line.split(':')[0] + Input.SHORT_SYMBOL + "/" + line.split('/')[1] + "\n"
                    elif(Input.LONG_SYMBOL in line):
                        newLine = line.split(':')[0] + Input.LONG_SYMBOL + "/" + line.split('/')[1] + "\n"
                    else:
                        newLine = line.split(':')[0] + "/" + line.split('/')[1] + "\n"

                    if(newLine not in optimisedDot):
                        optimisedDot += newLine
                else:
                    optimisedDot = optimisedDot + line + "\n"
                    
            # add the line if there is no initial Client Hello input
            else:
                optimisedDot = optimisedDot + line + "\n"
        # add the line if there it is not a state transition
        else:
            optimisedDot = optimisedDot + line + "\n"

    #print(optimisedDot)
    return optimisedDot

# create a new dot file for saving
def writeDotToFile(dotFile, dot, isOptimisedDot=True):
    if(isOptimisedDot):
        newDotFile = dotFile.rsplit('/', 1)[0]
        newDotFile += "/optimisedLearnedModel.dot"
    else:
        newDotFile = dotFile

    with open(newDotFile, "w") as file:
        file.writelines(dot)

    return newDotFile

# remove state transitions that cannot lead to a new state.
# optimise function after S&P'24
def optimiseDotFile(dotFile):
    with open(dotFile, "r") as file:
        dot = file.readlines()
    
    optimisedDot = ""

    # only take those state transitions that move on to a new state 
    # merge state transitions that does not move on to the new state into one
    for line in dot:
        if ("->" in line and not "label=\"\"" in line and not "__start0" in line):
            data = line.split()

            # transition to new state, ignore if self-loop
            if(data[0] != data[2]):
                previousState = data[0]
                nextState = data[2]
                input = data[3].split('/')[0].split('"')[1]
                inputType = input.split('_')[0]
                output = data[3].split('/')[1]
                isMerge = False
                

                # ignore if the invalid input lead to a connectionClose
                # if(not ((inputType == Input.HANDSHAKE_EMPTY_CERTIFICATE or inputType == Input.HANDSHAKE_INVALID_CERTIFICATE or 
                #     inputType == Input.INVALID_NEW_CONNECTION_ID) and output == Output.NORMAL_CONNECTION_CLOSE)):
                for line2 in dot:
                    if ("->" in line2 and not "label=\"\"" in line2 and not "__start0" in line2):
                        data2 = line2.split()
                        previousState2 = data2[0]
                        nextState2 = data2[2]
                        input2 = data2[3].split('/')[0].split('"')[1]
                        inputType2 = input2.split('_')[0]
                        output2 = data2[3].split('/')[1]

                        # same previous and next states; same inputType (Except Initial Client Hello)
                        if(previousState == previousState2 and nextState == nextState2 and inputType == inputType2 and 
                            input != input2 and output == output2):
                            isMerge = True
                            #print(line)
                            
                            newLine = line.split('_')[0] + "/" + line.split('/')[1]

                            if(newLine not in optimisedDot):
                                optimisedDot += newLine
                                #print(newLine)

                            break                
                if(not isMerge):
                    optimisedDot += line
                #optimisedDot += line
        else:
            optimisedDot += line

    # merge initial Client Hello wth different cipher suite here
    lines = optimisedDot.splitlines()
    optimisedDot = ""

    for line in lines:
        if ("->" in line and not "label=\"\"" in line and not "__start0" in line):
            data = line.split()
            previousState = data[0]
            nextState = data[2]
            input = data[3].split('/')[0].split('"')[1]
            output = data[3].split('/')[1]
            
            # merge initialClientHello-validACK
            if(Input.INITIAL_CLIENT_HELLO_VALID_ACK in line):
                allSame = 1

                for line2 in lines:
                    if ("->" in line2 and not "label=\"\"" in line2 and not "__start0" in line2):
                        data2 = line2.split()
                        previousState2 = data2[0]
                        nextState2 = data2[2]
                        input2 = data2[3].split('/')[0].split('"')[1]
                        output2 = data2[3].split('/')[1]

                        # if 3 of the ciphger suite lead to same nextState from same previousState and have same output, merge them
                        if(Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_128_GCM_SHA256 in input):
                            if(Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_256_GCM_SHA384 in input2 or Input.INITIAL_CLIENT_HELLO_VALID_ACK_CHACHA20_POLY1305_SHA256 in input2):
                                if(previousState == previousState2 and nextState == nextState2 and 
                                        input != input2 and output == output2):
                                    allSame += 1
                        elif(Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_256_GCM_SHA384 in input):
                            if(Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_128_GCM_SHA256 in input2 or Input.INITIAL_CLIENT_HELLO_VALID_ACK_CHACHA20_POLY1305_SHA256 in input2):
                                if(previousState == previousState2 and nextState == nextState2 and 
                                        input != input2 and output == output2):
                                    allSame += 1
                        elif(Input.INITIAL_CLIENT_HELLO_VALID_ACK_CHACHA20_POLY1305_SHA256 in input):
                            if(Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_128_GCM_SHA256 in input2 or Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_256_GCM_SHA384 in input2):
                                if(previousState == previousState2 and nextState == nextState2 and 
                                        input != input2 and output == output2):
                                    allSame += 1
                        
                        if(allSame == 3):
                            break
                
                # there is at most 3 cipher suites so make sure it does not exceed 3
                assert(allSame < 4)
                
                # merge them, if they has short or long symbol, keep it
                if(allSame == 3):
                    if(Input.SHORT_SYMBOL in line):
                        newLine = line.split(':')[0] + Input.SHORT_SYMBOL + "/" + line.split('/')[1] + "\n"
                    elif(Input.LONG_SYMBOL in line):
                        newLine = line.split(':')[0] + Input.LONG_SYMBOL + "/" + line.split('/')[1] + "\n"
                    else:
                        newLine = line.split(':')[0] + "/" + line.split('/')[1] + "\n"

                    if(newLine not in optimisedDot):
                        optimisedDot += newLine
                else:
                    optimisedDot = optimisedDot + line + "\n"

            # merge initialClientHello-invalidACK
            elif(Input.INITIAL_CLIENT_HELLO_INVALID_ACK in line):
                allSame = 1

                for line2 in lines:
                    if ("->" in line2 and not "label=\"\"" in line2 and not "__start0" in line2):
                        data2 = line2.split()
                        previousState2 = data2[0]
                        nextState2 = data2[2]
                        input2 = data2[3].split('/')[0].split('"')[1]
                        output2 = data2[3].split('/')[1]

                        # if 3 of the ciphger suite lead to same nextState from same previousState and have same output, merge them
                        if(Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_128_GCM_SHA256 in input):
                            if(Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_256_GCM_SHA384 in input2 or Input.INITIAL_CLIENT_HELLO_INVALID_ACK_CHACHA20_POLY1305_SHA256 in input2):
                                if(previousState == previousState2 and nextState == nextState2 and 
                                        input != input2 and output == output2):
                                    allSame += 1
                        elif(Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_256_GCM_SHA384 in input):
                            if(Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_128_GCM_SHA256 in input2 or Input.INITIAL_CLIENT_HELLO_INVALID_ACK_CHACHA20_POLY1305_SHA256 in input2):
                                if(previousState == previousState2 and nextState == nextState2 and 
                                        input != input2 and output == output2):
                                    allSame += 1
                        elif(Input.INITIAL_CLIENT_HELLO_INVALID_ACK_CHACHA20_POLY1305_SHA256 in input):
                            if(Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_128_GCM_SHA256 in input2 or Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_256_GCM_SHA384 in input2):
                                if(previousState == previousState2 and nextState == nextState2 and 
                                        input != input2 and output == output2):
                                    allSame += 1
                        
                        if(allSame == 3):
                            break
                
                # there is at most 3 cipher suites so make sure it does not exceed 3
                assert(allSame < 4)
                
                # merge them, if they has short or long symbol, keep it
                if(allSame == 3):
                    if(Input.SHORT_SYMBOL in line):
                        newLine = line.split(':')[0] + Input.SHORT_SYMBOL + "/" + line.split('/')[1] + "\n"
                    elif(Input.LONG_SYMBOL in line):
                        newLine = line.split(':')[0] + Input.LONG_SYMBOL + "/" + line.split('/')[1] + "\n"
                    else:
                        newLine = line.split(':')[0] + "/" + line.split('/')[1] + "\n"

                    if(newLine not in optimisedDot):
                        optimisedDot += newLine
                else:
                    optimisedDot = optimisedDot + line + "\n"
                    
            # add the line if there is no initial Client Hello input
            else:
                optimisedDot = optimisedDot + line + "\n"
        # add the line if there it is not a state transition
        else:
            optimisedDot = optimisedDot + line + "\n"

    #print(optimisedDot)
    return optimisedDot

# create a new dot file for saving
def writeDotToFileChecking(dotFile, optimisedDot):
    newDotFile = dotFile.rsplit('/', 1)[0]
    newDotFile += "/checking_1.dot"

    with open(newDotFile, "w") as file:
        file.writelines(optimisedDot)

    return newDotFile

# merge state transitions that does not move on to the new state into one
#def mergeStateTransition(optimisedDot):
#    for line in optimisedDot:
#    return optimisedDot



def main():
    # this main function will convert a dot file to a pdf
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dot", 
                        help="dot file")

    args = parser.parse_args()

    # optimisedDot = optimiseDotFile(args.dot)
    #optimisedDot = mergeStateTransition(optimisedDot)
    # newDotFile = writeDotToFile(args.dot, optimisedDot)

    optimisedDot = optimiseDotFile(args.dot)
    newDotFile = writeDotToFile(args.dot, optimisedDot, isOptimisedDot=True)

    newPdfFile = newDotFile.rsplit(".", 1)[0]
    automaton = load_automaton_from_file(newDotFile, "mealy")

    visualize_automaton(automaton, path=newPdfFile)
   
    print("Successfully optimised this learned model.")

if __name__ == "__main__":
    main()