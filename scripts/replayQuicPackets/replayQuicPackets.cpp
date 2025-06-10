//author: Kian Kai Ang

#include <iostream>
#include <string>
#include <fstream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <cstdio>
#include <chrono>
#include <thread>

// see https://github.com/jarro2783/cxxopts/blob/master/INSTALL
#include "cxxopts.hpp"

using namespace std;

const char* GREEN = "\033[32m";
const char* RESET = "\033[0m";

// tshark -r pingServerToDeath.pcap -qz "conv,udp" | grep '8999' | wc -l
// tshark -r pingServerToDeath.pcap -z "follow,udp,raw,0" -q | head -n -1 | tail -n +7

// show the progress of the current task
void updateProgressBar(int progress, int total) {
    int barWidth = 50;
    float progressRatio = static_cast<float>(progress) / total;
    int pos = barWidth * progressRatio;

    cout << "[";
    for (int i = 0; i < barWidth; ++i) {
        if (i < pos)
            cout << "=";
        else if (i == pos)
            cout << ">";
        else
            cout << " ";
    }
    cout << "] " << int(progressRatio * 100.0) << "%\r";
    cout.flush();
}

// extract QUIC Initial Ping from pcap
int extractInitialPingPacket(string pcapFile, string outputFile){
    // get the number of streams (row) of in the pcap file
    string GetStreamNumCommand = "tshark -r " + pcapFile + " -qz 'conv,udp' | grep '<->' | wc -l";

    FILE* pipe = popen(GetStreamNumCommand.c_str(), "r");
    if (!pipe) {
        cerr << "popen() failed." << endl;
        return 1;
    }

    string pipeOutput;
    char buffer[128];
    while (true) {
        if (fgets(buffer, sizeof(buffer), pipe) != NULL) {
            pipeOutput += buffer;
        }else{
            break;
        }
    }

    pclose(pipe);

    // extract the Udp payload (QUIC packet) stream by stream
    int numOfStream = stoi(pipeOutput);
    string extractQuicPktCommand1 = "tshark -r " + pcapFile + " -z 'follow,udp,raw,";
    string extractQuicPktCommand2 = "' -q | head -n -1 | tail -n +7 | xxd -r -p >> " + outputFile;

    cout << "Extracting QUIC packets..." << endl;

    // extract the QUIC packet one by one (by udp streams)
    for(int i=0; i<numOfStream; i++){
        updateProgressBar(i, numOfStream);
        string completeCommand = extractQuicPktCommand1 + to_string(i) + extractQuicPktCommand2;

        if(system(completeCommand.c_str()) != 0){
            cerr << "Not able to extract" << endl;
            return 1;
        }
    }

    cout << endl << GREEN << "Done." << RESET << endl;

    return 0;
}

// replay QUIC Initial Ping from raw
int replayPacket(string rawFile, string ipAddr, int port){
    // server information
    struct sockaddr_in serverAddr;
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(port); // Replace with the port you want to send data to
    serverAddr.sin_addr.s_addr = inet_addr(ipAddr.c_str()); // Replace with the server's IP address

    // open the binary file for reading
    ifstream file(rawFile, ios::in | ios::binary);

    if (!file.is_open()) {
        cerr << "Failed to open the input file." << endl;
        return 1;
    }

    // get file size
    file.seekg(0, std::ios::end);
    streampos fileSize = file.tellg();
    file.seekg(0, std::ios::beg);
    const int initialPacketSize = 1280;
    int fileSizeInt = static_cast<int>(fileSize);
    int packetCount = fileSizeInt/initialPacketSize;
    int count=0;
    int clientPort = 10000;

    cout << "Replaying QUIC packets..." << endl;

    while (true) {
        // get the Initial 
        char *packet = new char[initialPacketSize];
        file.read(packet, initialPacketSize);
        
        // client socket config
        int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
        struct sockaddr_in clientAddr;
        clientAddr.sin_family = AF_INET;
        clientAddr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
        int ret;

        // create a socket and blind to a specific port
        if (sockfd < 0) {
            perror("Socket creation failed");
            return 1;
        }else{
            do{
                if(clientPort >= 65535){
                    clientPort = 10000;
                }else{
                    clientPort++;
                }

                clientAddr.sin_port = htons(clientPort);
                ret = ::bind(sockfd, (struct sockaddr*)&clientAddr, sizeof(clientAddr));

            }while(ret != 0);
        }

        // send data over the UDP socket
        ssize_t bytesSent = sendto(sockfd, packet, initialPacketSize, 0, (struct sockaddr*)&serverAddr, sizeof(serverAddr));
        this_thread::sleep_for(chrono::microseconds(500));
        // close the socket
        close(sockfd);

        count++;
        updateProgressBar(count, packetCount);

        if (bytesSent < 0) {
            perror("Sendto failed");
            break;
        }

        if (file.eof()) {
            break; // End of file reached
        }
    }

    cout << endl << GREEN << "Done." << RESET << endl;

    file.close();

    return 0;
}

// main
int main(int argc, char* argv[]) {
    cxxopts::Options options("replayQuicPackets", "A program that can extract QUIC packets from pcap and replay it to a server.\nDO NOT USE WHEN THE QUIC SECRET LOG IS VERY BIG (>200MB).");

    int port;
    string filePath, ipAddr, outputPath;

    options.add_options()
    ("x,extract", "Pcap file to extract Initial Ping packets and save it to the output file (-o).", cxxopts::value<string>(filePath))
    ("o, output", "Output file to store the extracted Raw (use with -x).", cxxopts::value<string>(outputPath)->default_value("extracted.raw"))
    ("r,replay", "Raw file to replay the extracted Initial Ping packets.", cxxopts::value<string>(filePath))
    ("i, ip", "Server IP Address (use with -r).", cxxopts::value<string>(ipAddr)->default_value("127.0.0.1"))
    ("p, port", "Server port (use with -r).", cxxopts::value<int>(port)->default_value("8999"))
    ("h, help", "Print help");
    
    try{
        auto result = options.parse(argc, argv);

        if(result.count("help")){
            cout << options.help({""}) << endl;
            return 0;
        }

        if(result.count("extract")){
            extractInitialPingPacket(filePath, outputPath);
        }else if(result.count("replay")){
            replayPacket(filePath, ipAddr, port);
        }

    }
    catch (const cxxopts::exceptions::exception& e)
    {
        cerr << "error parsing options: " << e.what() << endl;
        cout << options.help({""}) << endl;
        return 0;
    }

    return 0;
}