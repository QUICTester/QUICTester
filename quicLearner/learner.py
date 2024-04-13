# 

from ast import arg
import os
import signal
import time
import subprocess
import sys
import argparse
from turtle import dot
from unittest import result
import atexit
import datetime
import shutil

from aalpy.base import SUL
from aalpy.oracles import RandomWalkEqOracle
from aalpy.oracles.WMethodEqOracle import RandomWMethodEqOracle, WMethodEqOracle
from aalpy.learning_algs import run_Lstar
from aalpy.utils import visualize_automaton
from aalpy.utils.FileHandler import save_automaton_to_file, load_automaton_from_file

# added to use learnlib
from py4j.java_gateway import JavaGateway, CallbackServerParameters, GatewayParameters, launch_gateway
from py4j.protocol import Py4JJavaError

sys.path.insert(0, "../quicMapper/")
from inOutPut import Input, Server, InputDictionary
from optimiseModel import writeDotToFile, optimiseDotFile

# use for result saving at the end of the learning
INPUT_ALPHABET = []
OUTPUT_ALPHABET = []
MESSAGE_CHAIN_COUNT = 0

class QUIC_SUL(SUL):
    def __init__(self, args):
        super().__init__()

        # store all the input.txt and output.txt in this folder
        self.runFolder = "run/"
        if(not os.path.exists(self.runFolder)):
            os.mkdir(self.runFolder)

       # arguements to run the target QUIC server
        self.serverLog = self.runFolder + "server_" + args.port + ".log"
        self.serverCmd = args.run + " >> " + self.serverLog + " 2>&1"
        self.targetServer = args.server
        if(args.config != ""):
            self.config = args.config
        else:
            self.config = ""

        # arguements to run mapper
        if(args.docker):
            self.mapperPython = "python3"
        else:
            self.mapperPython = "../quicMapper/env/bin/python"
        
        self.mapperPath = " ../quicMapper/mapper.py"
        #self.mapperPath = " ../quicMapper/mapperOld.py"
        self.mapperArgs = ""
        self.mapperLog = self.runFolder + "mapper_" + args.port + ".log"

        # remove mapper log
        #if(os.path.exists(self.mapperLog)):
        #    cmd = "rm " + self.mapperLog
        #    os.system(cmd)
        
        self.mapperArgs = "-s " + args.server

        # add mapper port and target port to mapper args
        self.mapperArgs = self.mapperArgs + " -p " + args.port + " -t " + args.targetPort

        # adding client certificate and public key
        if(args.cert and args.key):
            self.mapperArgs = self.mapperArgs + " -c " + args.cert + " -k " + args.key
        
        # adding invalid certificate
        if(args.invalidCertificate):
            self.mapperArgs = self.mapperArgs + " --invalidCertificate " + args.invalidCertificate

        # adding CA cert
        if(args.caCert):
            self.mapperArgs = self.mapperArgs + " --caCert " + args.caCert

        # adding secrets file
        if(args.secrets):
            self.mapperArgs = self.mapperArgs + " --secrets " + args.secrets

        # tell mapper which input dictionary is used, so it can allocate different timeout for neqo and s2n during retry (because of their token expiry too short)
        if(self.targetServer == Server.NEQO or self.targetServer == Server.S2NQUIC):
            self.mapperArgs = self.mapperArgs + " -i " + args.input

        # each fuzzing need to have unique sessionTicket file
        self.sessionTicket = self.runFolder + "sessionTicket_" + args.port
        self.mapperArgs = self.mapperArgs + " --sessionTicket " + self.sessionTicket

        # get the session ticket before each fuzzing iteration
        if("PSK" in args.input):
            self.mapperArgs = self.mapperArgs + " --getSessionTicket "

        # adding count flag
        self.mapperArgs += " --count "
        
        # adding log file
        if(args.log):
            self.showMapperLog = True
        else:
            self.showMapperLog = False

        self.inputPath = self.runFolder + "input_" + args.port + ".txt"
        self.outputPath = self.runFolder + "output_" + args.port + ".txt"
        self.outputCount = 0
        self.serverProcess = None
        self.mapperProcess = None
        self.inputSequence = []
        self.crashCount = 0
        self.crashInputSequences = []

    # remove input.txt & output.txt
    # setup and run mapper
    def pre(self):
        global MESSAGE_CHAIN_COUNT

        # if the server is not alive/crash:
        # remove the old sessionTicket so that the Mapper will get a new one when the server is restarted
        if(not self.isSUTAlive()):
            if(os.path.exists(self.sessionTicket)):
                os.remove(self.sessionTicket)

        # check if the server is alive 
        # start quic server if it is not
        while(not self.isSUTAlive()):
            print("Server is not alive, starting the server...")
            self.serverProcess = subprocess.Popen(self.serverCmd, shell=True, preexec_fn=os.setsid)
            time.sleep(0.5)

        self.outputCount = 0

        if(os.path.exists(self.inputPath)):
            cmd = "rm " + self.inputPath
            os.system(cmd)

        if(os.path.exists(self.outputPath)):
            cmd = "rm " + self.outputPath
            os.system(cmd)

        MESSAGE_CHAIN_COUNT += 1
        print("msg chain count = " + str(MESSAGE_CHAIN_COUNT))

        # start the mapper
        self.startMapper()

    # tell the mapper it is the end
    def post(self):
        with open(self.inputPath, "a") as inFile:
            inFile.write("end\n")
        
        if(not self.isSUTAlive()):
            print("Server is not alive. Maybe #" + str(MESSAGE_CHAIN_COUNT) + " input sequence crashed the server?")
            self.crashCount += 1
            if(self.inputSequence not in self.crashInputSequences):
                self.crashInputSequences.append(self.inputSequence)
        
        print(self.inputSequence)
        self.inputSequence = []

        # kill the server everytime for QUICHE, QUANT and S2N
        # will always remove and get the session ticket before each iteration.
        if(self.targetServer == Server.QUICHE or self.targetServer == Server.S2NQUIC or self.targetServer == Server.QUANT or self.targetServer == Server.PQUIC):
            #"""# kill the server
            try:
                # kill quic server
                os.killpg(os.getpgid(self.serverProcess.pid), signal.SIGTERM)
                time.sleep(0.5)
            except:
                print("ERROR: Failed to kill the server.")
            #"""
        
        # kill mapper
        #time.sleep(1)
        # self.mapperProcess.kill() # not working
        os.killpg(os.getpgid(self.mapperProcess.pid), signal.SIGTERM)

        # check if the server log has exceed the 50 MB (delete the log if yes)
        # then create an empty file
        if(os.path.exists(self.serverLog)):
            if(os.stat(self.serverLog).st_size > (50 * 1024 * 1024)):
                os.remove(self.serverLog)
                with open(self.serverLog, 'w') as newServerLog:
                    pass
        
    # write input to input.txt
    # read output from output.txt
    def step(self, letter):
        self.inputSequence.append(letter)

        # add new input
        with open(self.inputPath, "a") as inFile:
            inFile.write(letter + "\n")

        outputList = []
        output = ""

        # waiting for all output
        while output != "end":
            try:
                # if the mapper is dead, re-start the mapper and refuzz the current input
                if(not self.isMapperAlive()):
                    # self.outputCount = 0
                    # outputList = []
                    # output = ""
                    
                    # # get the outputCount of the last "end", so that the learner know when is the output for the refuzz input
                    # with open(self.outputPath, "r") as outFile:
                    #     for lineNum, line in enumerate(outFile, start=1):
                    #         if(line.split("\n")[0] == "end"):
                    #             self.outputCount = lineNum

                    # remove the output file
                    if(os.path.exists(self.outputPath)):
                        cmd = "rm " + self.outputPath
                        os.system(cmd)
                    
                    # refuzz this input
                    self.startMapper()
                else:    
                    with open(self.outputPath, "r") as outFile:
                        lines = outFile.readlines()

                        if(len(lines) > self.outputCount):
                            output = lines[self.outputCount].split("\n")[0]
                            self.outputCount += 1

                            if(output != "end"):
                                outputList.append(str(output))

                                if(output not in OUTPUT_ALPHABET):
                                    OUTPUT_ALPHABET.append(output)

            except:
                continue

        output = ""
        
        # combine all output into one string
        for i in range(len(outputList)):
            if(i > 0):
                output = output + "," + outputList[i]
            else:
                output = outputList[i]

        output += " "

        return output

    # Check if the SUT is alive or not
    def isSUTAlive(self):
        #return False
        if(self.serverProcess == None):
            return False

        time.sleep(0.5)
        if(self.serverProcess.poll() == None):
            return True
        else:
            return False

    def isMapperAlive(self):
        if(self.mapperProcess == None):
            return False

        if(self.mapperProcess.poll() == None):
            return True
        else:
            return False
        
    def startMapper(self):
        cmd = self.mapperPython + " " + self.mapperPath + " " + self.mapperArgs + str(MESSAGE_CHAIN_COUNT)

        # start mapper
        while(not self.isMapperAlive()):
            if(self.showMapperLog):
                #show mapper output
                self.mapperProcess = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
            else:
                # do not show mapper output
                #cmd = cmd + " >> " + self.mapperLog + " 2>&1 "
                self.mapperProcess = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid
                                        ,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
                
            time.sleep(0.5)

            # check if the mapper is up
            if(not self.isMapperAlive()):
                print("ERROR: Failed to start the Mapper.")

    # for learnlib
    def canFork(self):
        return False
    
    # for learnlib
    def fork(self): pass

    # for learnlib
    class Java:
        implements = ["de.learnlib.api.SUL"]

# start and run the Java gateway server
def startJavaGatewayServer(args, sul):
    # start the java gateway server
    gatewayServerPort = int(args.port) + 10000
    gatewayClientPort = int(args.targetPort) + 10000

    # check if the ports are used
    cmd = "lsof -i:" + str(gatewayServerPort)
    errorStr = "Port " + str(gatewayServerPort) + " is in use."
    lsofOutput = os.popen(cmd).read()
    assert(lsofOutput == ""), errorStr
    cmd = "lsof -i:" + str(gatewayClientPort)
    errorStr = "Port " + str(gatewayClientPort) + " is in use."
    lsofOutput = os.popen(cmd).read()
    assert(lsofOutput == ""), errorStr

    gatewayLogPath = sul.runFolder + "gateserver_" + str(gatewayServerPort) + ".log"
    gatewayServerCmd = "java -jar ../learnlib-py4j-example/java/target/learnlib-py4j-example-1.0-SNAPSHOT.jar " + str(gatewayServerPort) + " " + str(gatewayClientPort) + " > " + gatewayLogPath + " 2>&1" 
    gatewayProcess = subprocess.Popen(gatewayServerCmd, shell=True, preexec_fn=os.setsid)
    time.sleep(1)

    return gatewayProcess

# convert the input list to java list format
def convertToJavaList(gateway, inputAlphabet):
    # Access the java.util.ArrayList class and create a new Java ArrayList
    array_list_class = gateway.jvm.java.util.ArrayList
    java_list = array_list_class()

    # Add elements from the Python list to the Java ArrayList
    for item in inputAlphabet:
        java_list.add(item)

    return gateway.jvm.net.automatalib.words.impl.Alphabets.fromList(java_list)

# convert Automaton generated from LearnLib to the format understand by the Learner
def formatLearnLibAutomaton(gateway, hyp, inputAlphabet):
    # Construct a buffer that we will use to print results on the Python side of our setup
    string_writer = gateway.jvm.java.io.StringWriter()
    gateway.jvm.net.automatalib.serialization.dot.GraphDOT.write(hyp, inputAlphabet, string_writer)

    learned_quic = string_writer.toString()
    learned_quic = learned_quic.replace('\t', '')
    learned_quic = learned_quic.replace(' / ', '/')

    return learned_quic

# Close connection with Java gateway server and kill it
def killJavaGatewayServer(gatewayProcess):
    if(gatewayProcess.poll() == None):
        os.killpg(os.getpgid(gatewayProcess.pid), signal.SIGTERM)

def createResultFolder(args, learned_quic, stat, inputAlpha, outputAlpha, sul):
    if(args.config != ""):
        resultName = args.server + "-" + args.config + "-" + args.input
    else:
        resultName = args.server + "-" + args.input
    resultPath = "../results/" + args.server + "Models/"

    if(not os.path.exists(resultPath)):
        os.mkdir(resultPath)

    i = 0
    while os.path.exists(resultPath + resultName + "-%s" % i):
        i += 1

    resultPath = resultPath + resultName + "-%s" % i
    os.mkdir(resultPath)
    learnedModelPath = resultPath + "/learnedModel"
    infoPath = resultPath + "/stat.txt"
    dotFile = learnedModelPath + ".dot"

    if(not args.learnlib):
        # save the state diagram into a .dot file
        save_automaton_to_file(learned_quic, path=learnedModelPath)
    else:
        dotFile = writeDotToFile(dotFile=dotFile, dot=learned_quic, isOptimisedDot=False)
        learned_quic = load_automaton_from_file(dotFile, "mealy")

    # save the learned model in results/XXX-[int]/LearnedModel.pdf
    visualize_automaton(learned_quic, path=learnedModelPath)

    # optimise the learnt model
    optimisedDot = optimiseDotFile(dotFile=dotFile)
    newDotFile = writeDotToFile(dotFile=dotFile, dot=optimisedDot, isOptimisedDot=True)
    optimisedPdfFile = newDotFile.rsplit(".", 1)[0]
    automaton = load_automaton_from_file(newDotFile, "mealy")
    visualize_automaton(automaton, path=optimisedPdfFile)

    # Get current time
    currentTime = datetime.datetime.now()

    # save input and output alphabet
    with open(infoPath, "w") as file:
        file.write("Input Alphabets: \n")

        for alphabet in inputAlpha:
            file.write(alphabet + "\n")

        file.write("\n\n")

        file.write("Output Alphabets: \n")

        for alphabet in outputAlpha:
            file.write(alphabet + "\n")

        file.write("\n\n")
        file.write("Date: " + str(currentTime) + "\n" )
        file.write("Input Dictionary: " + args.input + "\n")
        file.write("Target server port: " + args.targetPort + "\n")
        file.write("Mapper port: " + args.port + "\n")
        if(stat != None):
            file.write(stat)
        file.write("Crash Count: " + str(sul.crashCount) + "\n\n")
        file.write("Crash Input Sequences: \n")
        for inputSequence in sul.crashInputSequences:
            file.write(str(inputSequence) + "\n")

    # move the learner log and server log to the result
    learnerLogPath = sul.runFolder + "learner_" + args.server + "_" + args.input + "_" + args.port + ".log"
    newLearnerLogPath = resultPath + "/learner.log"
    serverLogPath = sul.serverLog
    newServerLogPath = resultPath + "/server.log"

    try:
        shutil.move(learnerLogPath, newLearnerLogPath)
        shutil.move(serverLogPath, newServerLogPath)
    except:
        pass
    
    # move the gateway server log
    if(args.learnlib):
        gatewayServerPort = int(args.port) + 10000
        gatewayServerLog =  sul.runFolder + "gateserver_" + str(gatewayServerPort) + ".log"
        newGatewayServerLog = resultPath + "/gateway.log"

        try:
            shutil.move(gatewayServerLog, newGatewayServerLog)
        except:
            pass

    # remove unused file (input.txt and output.txt)
    if(os.path.exists(sul.inputPath)):
            cmd = "rm " + sul.inputPath
            os.system(cmd)

    if(os.path.exists(sul.outputPath)):
            cmd = "rm " + sul.outputPath
            os.system(cmd)


# shutdown the mapper and server before program ends
# auto shutdown mapper and server when non-deterministic
def exitHandler(sul):
    time.sleep(1)
    
    # kill the mapper and server
    os.killpg(os.getpgid(sul.mapperProcess.pid), signal.SIGTERM)
    os.killpg(os.getpgid(sul.serverProcess.pid), signal.SIGTERM)

def signalHandler(signum, frame):
    sys.exit(1)

def checkServerFile(sul):
    try:
        with open(sul.serverLog, 'r') as file:
            log = file.readlines()
    
        if("Segmentation fault" in log):
            print("ATTENTION: Server does crash during fuzzing....")
    except FileNotFoundError:
        print("Error: Server log not found.")

# main function
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--server", choices=Server.LIST, 
                        required=True, help="target QUIC server")
    parser.add_argument("-i", "--input", choices=["B", "BWR", "BWCA", "BWRCA", "B-s", "BWR-s", "BWCA-s", "BWRCA-s", "B-l", "BWR-l", "BWCA-l", "BWRCA-l", "PSK", "PSK-s", "PSK-l", "PSKWR", "PSKWR-s", "PSKWR-l"], 
                        required=True, help="input dictionary: B(basic), BWR(B + retry), BWCA(B + client authentication), BWRCA(BWCA + retry)")
    parser.add_argument("--config", choices=["B", "BWR", "BWCA", "BWRCA", "PSK"], default="", 
                        help="config: B(basic), BWR(B + retry), BWCA(B + client authentication), BWRCA(BWCA + retry)")
    parser.add_argument("-p", "--port", type=str,
                        default="3344",
                        help="mapper port")
    parser.add_argument("-t", "--targetPort", type=str,
                        default="4433",
                        help="target port")
    parser.add_argument("-c", "--cert", 
                        default="../secrets/clientCert/client-cert.pem",
                        help="valid client certificate for client authentication")
    parser.add_argument("-k", "--key", 
                        default="../secrets/clientCert/client-key.pem",
                        help="valid client public key for client authentication")
    parser.add_argument("--invalidCertificate", type=str, 
                        default="../secrets/invalidCert/invalid-cert.pem",
                        help="load the invalid certificate from the specified file")
    parser.add_argument("--caCert", type=str, 
                        default="../secrets/caCert/ca-cert.pem",
                        help="CA cert for verify peer certificate")
    parser.add_argument("--secrets", type=str, 
                        default="../secrets/mapperSecrets.log",
                        help="file to store the secrets (use in Wireshark late)")
    parser.add_argument("--log", action="store_true", 
                        help="show mapper's log")
    parser.add_argument("-r", "--run", required=True,
                        help="command to run the target server")
    parser.add_argument("--docker", action="store_true", default=False,
                        help="Running Learner and Mapper in Docker")
    parser.add_argument("--learnlib", action="store_true", default=False,
                        help="Use LearnLib instead of AALPY")

    args = parser.parse_args()

    # kill the Learner, Mapper, Server, Java Gateway Server gracefully
    signal.signal(signal.SIGTERM, signalHandler)

    # validate if the ports is used
    cmd = "lsof -i:" + args.port
    errorStr = "Port " + args.port + " is in use."
    lsofOutput = os.popen(cmd).read()
    assert(lsofOutput == ""), errorStr
    cmd = "lsof -i:" + args.targetPort
    errorStr = "Port " + args.targetPort + " is in use."
    lsofOutput = os.popen(cmd).read()
    assert(lsofOutput == ""), errorStr

    # mapper configuration
    sul = QUIC_SUL(args)
    stat = None
    learned_quic = None
    gateway = None

    if(os.path.exists(sul.serverLog)):
        cmd = "rm " + sul.serverLog
        os.system(cmd)

    if(args.input == "B"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.BASIC, timeout=None)
    elif(args.input == "BWR"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.BASIC_WITH_RETRY, timeout=None)
    elif(args.input == "BWCA"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.BASIC_WITH_CA, timeout=None)
    elif(args.input == "BWRCA"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.BASIC_WITH_RETRY_CA, timeout=None)
    elif(args.input == "PSK"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.PSK, timeout=None)
    elif(args.input == "B-s"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.BASIC, timeout=Input.SHORT_SYMBOL)
    elif(args.input == "BWR-s"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.BASIC_WITH_RETRY, timeout=Input.SHORT_SYMBOL)
    elif(args.input == "BWCA-s"):
       INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.BASIC_WITH_CA, timeout=Input.SHORT_SYMBOL)
    elif(args.input == "BWRCA-s"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.BASIC_WITH_RETRY_CA, timeout=Input.SHORT_SYMBOL)
    elif(args.input == "B-l"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.BASIC, timeout=Input.LONG_SYMBOL)
    elif(args.input == "BWR-l"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.BASIC_WITH_RETRY, timeout=Input.LONG_SYMBOL)
    elif(args.input == "BWCA-l"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.BASIC_WITH_CA, timeout=Input.LONG_SYMBOL)
    elif(args.input == "BWRCA-l"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.BASIC_WITH_RETRY_CA, timeout=Input.LONG_SYMBOL)
    elif(args.input == "PSK-s"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.PSK, timeout=Input.SHORT_SYMBOL)
    elif(args.input == "PSK-l"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.PSK, timeout=Input.LONG_SYMBOL)
    elif(args.input == "PSKWR-s"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.PSK_WITH_RETRY, timeout=Input.SHORT_SYMBOL)
    elif(args.input == "PSKWR-l"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.PSK_WITH_RETRY, timeout=Input.LONG_SYMBOL)
    elif(args.input == "PSKWR"):
        INPUT_ALPHABET = InputDictionary.generateInputDictionary(baseDictionary=InputDictionary.PSK_WITH_RETRY, timeout=None)
    else:
        print("Error: Input dictionary not defined.")
        return 

    # add exit call back function
    atexit.register(exitHandler, sul)

    # dictionary for testing the whole run
    # INPUT_ALPHABET = InputDictionary.TEST

    # decide which learning library to use
    if(not args.learnlib):
        eq_oracle = RandomWalkEqOracle(INPUT_ALPHABET, sul, num_steps=20000, reset_after_cex=True, reset_prob=0.15)
        learned_quic, stat = run_Lstar(INPUT_ALPHABET, sul, eq_oracle=eq_oracle, automaton_type='mealy', cache_and_non_det_check=True,
                            print_level=3)
    else:
        gatewayProcess = startJavaGatewayServer(args, sul)
        gateway = JavaGateway(gateway_parameters=GatewayParameters(port=(int(args.port)+10000)), callback_server_parameters=CallbackServerParameters(port=(int(args.targetPort)+10000)))
        javaInputAlphabet = convertToJavaList(gateway, INPUT_ALPHABET)
        atexit.register(killJavaGatewayServer, gatewayProcess)

        random_class = gateway.jvm.java.util.Random
        random_num = random_class(46346293)
        learningAlgo = ""
        oracleType = ""
        
        statisticSul = gateway.jvm.de.learnlib.filter.statistic.sul.ResetCounterSUL("Membership queries", sul)
        effectiveSul = gateway.jvm.de.learnlib.filter.cache.sul.SULCaches.createCache(javaInputAlphabet, statisticSul)
        mq_oracle = gateway.jvm.de.learnlib.oracle.membership.SULOracle(effectiveSul)
        learningAlgo = "TTT Algorithm\n"
        ttt = gateway.jvm.de.learnlib.algorithms.ttt.mealy.TTTLearnerMealyBuilder().withAlphabet(javaInputAlphabet).withOracle(mq_oracle).create()
        oracleType = "Wp Method\n"
        
        if("BWR" in args.input):
            # use max-depth = 2 so that it will not get stuck when Retry is enabled
            eq_oracle = gateway.jvm.de.learnlib.oracle.equivalence.WpMethodEQOracle(mq_oracle, 2)
        else:
            eq_oracle = gateway.jvm.de.learnlib.oracle.equivalence.WpMethodEQOracle(mq_oracle, 1)
        
        experiment = gateway.jvm.de.learnlib.util.Experiment(ttt, eq_oracle, javaInputAlphabet)
        experiment.setProfile(True)
        startTime = datetime.datetime.now()

        try:
            experiment.run()
            # Get the final hypothesis of our SUL and write stats
            hyp = experiment.getFinalHypothesis()
            endTime = datetime.datetime.now()
            learningTime = (endTime - startTime).total_seconds() / 3600
            stat = "-----------------------------------\n" + learningAlgo + oracleType + experiment.getRounds().getSummary() + "\n" + "Number of states: " + str(hyp.size()) + "\n" + statisticSul.getStatisticalData().getSummary() + "\nTotal Learning Time (hours): " + str(learningTime) + "\n-----------------------------------\n"
            learned_quic = formatLearnLibAutomaton(gateway, hyp, javaInputAlphabet)
        except Py4JJavaError as e:
            print(e)
    
    # once the fuzzing is done, remove the remaining session ticket
    if(os.path.exists(sul.sessionTicket)):
        os.remove(sul.sessionTicket)

    if(learned_quic != None):
        checkServerFile(sul)
        createResultFolder(args, learned_quic, stat, INPUT_ALPHABET, OUTPUT_ALPHABET, sul)

    if(args.learnlib and gateway != None):
        gateway.shutdown()


if __name__ == "__main__":
    main()