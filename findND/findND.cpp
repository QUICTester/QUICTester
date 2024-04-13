// 

// usage: sudo ./findND serverName mapperPort ServerPort
// use mapperPort 5544 when tcpdump is enable

#include<iostream>
#include <string>
#include <algorithm>
#include <vector>
#include <sstream>
#include <iterator>
#include <stdio.h>
#include <fstream>
#include <unistd.h>
#include <sys/wait.h>

using namespace std;

string INPUT_FILE = "run/input_";
string OUTPUT_FILE = "run/output_";
string PREVIOUS_OUTPUT_FILE = "run/previousOutput_";

// run mapper
void runMapper(vector<string> inputSeq, string server, string mapperPort, string serverPort){
    string mapperPython = "../quicMapper/env/bin/python";
    string mapperPath = "../quicMapper/mapper.py";
    string mapperServerFlag = "-s";
    string mapperCert = "-c ../secrets/clientCert/client-cert.pem";
    string mapperKey = "-k ../secrets/clientCert/client-key.pem"; 

    // uncomment this if you want get the sessionTicket prior each iteration
    string mapperGetSessionTicket = " --getSessionTicket ";

    /*string strCmd = mapperPython + " " + mapperPath + " " + mapperServerFlag + " " + server +
                     " " + mapperCert + " " + mapperKey;
                     */
    string strCmd = mapperPython + " " + mapperPath + " " + mapperServerFlag + " " + server + " -p " + mapperPort + " -t " + serverPort + mapperGetSessionTicket;
    const char *cmd = strCmd.c_str();

    system(cmd);
}

void killMapper(string mapperPort){
    string cmd = "kill -9 $(lsof -t -i:" + mapperPort + ")";
    system(cmd.c_str());
}

// run tcpdump
void runTcpdump(int testCount, string mapperPort){
    //string runBackground = "gnome-terminal -q --window --title='tcpdump' -e 'bash -c \"";

    string runBackground = "";
    string tcpdump = "tcpdump";
    string interface = "-i lo";
    string port = "port " + mapperPort;
    string write = "-w capture.pcap";
    

    if(testCount == 1){
        write = "-w capture0.pcap";
    }
    
    string cmd = runBackground + tcpdump + " " + interface + " " + port + " " + write + " &";
    cout << cmd << endl;
    system(cmd.c_str());
}

void killTcpdump(){
    string cmd = "kill -2 $(ps -e | pgrep tcpdump)";
    system(cmd.c_str());
}

void openCapture(){
    string cmd = "wireshark capture.pcap";
    system(cmd.c_str());
}

// write input sequence to a file
void writeInputToFile(vector<string> inputSeq){
    ofstream inputFile(INPUT_FILE);

    for(unsigned long i=0; i<inputSeq.size(); i++){
        inputFile << inputSeq[i] << endl;
    }

    inputFile << "end";

    inputFile.close();
}

// create an empty output file for mapper
void createOutputFile(){
    ofstream outputFile(OUTPUT_FILE);
    outputFile.close();
}

// replace previous output with output
void toPreviousOutput(){
    // remove previous output
    string strCmd = "rm " + PREVIOUS_OUTPUT_FILE;
    const char *cmd = strCmd.c_str();
    system(cmd);

    // change output to previous output
    strCmd = "mv " + OUTPUT_FILE + " " + PREVIOUS_OUTPUT_FILE;
    cmd = strCmd.c_str();
    system(cmd);
}

// compare output and previous output
int isSameOutput(){
    ifstream output, previousOutput;

    output.open(OUTPUT_FILE);
    previousOutput.open(PREVIOUS_OUTPUT_FILE);

    string line;
    int outputLineCount = 0, previousOutputLineCount = 0;

    // compare if 2 files have the same amount of lines
    while (!output.eof())
    {
        getline(output, line);
        outputLineCount++;
    }

    while (!previousOutput.eof())
    {
        getline(previousOutput, line);
        previousOutputLineCount++;
    }

    // if line count not same return false
    if(outputLineCount != previousOutputLineCount){
        return 0;
    }

    output.clear();
    output.seekg(0, output.beg);
    previousOutput.clear();
    previousOutput.seekg(0, previousOutput.beg);

    string oLine;
    string pOLine;

    // compare line by line
    while(!output.eof()){
        getline(output, oLine);
        getline(previousOutput, pOLine);

        // return 0 if not same
        if(oLine != pOLine){
            output.close();
            previousOutput.close();
            return 0;
        }
    }

    output.close();
    previousOutput.close();

    return 1;
}

// main
int main(int argc, char **argv){
    string input, server = argv[1], mapperPort = argv[2], serverPort = argv[3];

    cout << "Input sequence: ";
    getline(cin, input);

    // remove open and close brackets
    input.erase(0, 1);
    input.erase(input.length()-1);

    // remove ""
    //boost::erase_all(input, "\"");
    input.erase(remove(input.begin(), input.end(), '\''), input.end());
    input.erase(remove(input.begin(), input.end(), ','), input.end());

    // change input and output file name
    INPUT_FILE = INPUT_FILE + mapperPort + ".txt";
    OUTPUT_FILE = OUTPUT_FILE + mapperPort + ".txt";
    PREVIOUS_OUTPUT_FILE = PREVIOUS_OUTPUT_FILE + mapperPort + ".txt";

    stringstream ss(input);
    istream_iterator<string> begin(ss);
    istream_iterator<string> end;
    vector<string> inputSeq(begin, end);

    writeInputToFile(inputSeq);

    bool nonDeterministic = false;
    int testCount = 0;

    while(!nonDeterministic){
        testCount++;
        runTcpdump(testCount, mapperPort);
        cout << "Test Count: " << testCount << endl;
        
        createOutputFile();
        runMapper(inputSeq, server, mapperPort, serverPort);
        int endCount = 0;
        
        while(endCount != inputSeq.size()){
            endCount = 0;
            ifstream output;
            string line;

            output.open(OUTPUT_FILE);

            while(!output.eof()){
                getline(output, line);

                if(line == "end"){
                    endCount++;
                }
            }
            
        }

        if(testCount > 1){
            if(!isSameOutput()){
                sleep(5);
                nonDeterministic = true;
            }else{
                toPreviousOutput();
            }
        }else{
            toPreviousOutput();
        }
        
        killMapper(mapperPort);

        killTcpdump();
        sleep(1);
    }

    //openCapture();

    return 0;
}