# 

import argparse
from ast import arg
import asyncio
from time import sleep, time, perf_counter
from urllib import response

from pkg_resources import require
import aioquic
import logging
import subprocess
import os
import signal
import sys
import pickle
from enum import Enum

import socket
from src.aioquic.quic.configuration import QuicConfiguration
from src.aioquic.h0.connection import H0_ALPN
from src.aioquic.h3.connection import H3_ALPN
from src.aioquic.quic.logger import QuicFileLogger
from src.aioquic.quic.connection import QuicConnection, END_STATES, MapperError
from src.aioquic.asyncio.protocol import QuicConnectionProtocol
from typing import cast
from src.aioquic import tls
from inOutPut import Input, Output, Server
from src.aioquic.quic.packet import QuicProtocolVersion

# print color text
def prRed(skk): print("\033[91m {}\033[00m" .format(skk))
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
def prCyan(skk): print("\033[96m {}\033[00m" .format(skk))

# disable printing at some point
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# resume printing at some point
def resumePrint():
    sys.stdout = sys.__stdout__

class Send0rttState(Enum):
    NOT_READY = 0  # havnt install PSK
    READY = 1      # installed PSK
    TOO_LATE = 2   # server may already discarded PSK (prevent non-deterministic)

class Mapper:
    def __init__(self, alpnProtocols, caCerts, secretsLog, quicLog, targetServer, targetHost, targetPort, localPort,
                 certificate, privateKey, invalidCertificate, shortTimeout, longTimeout, cipherSuite, quicVersion, isGetShortTimeout,
                 sessionTicket):
        # quic configurations
        self.configuration = QuicConfiguration(is_client=True, alpn_protocols=alpnProtocols)
        self.configuration.load_verify_locations(caCerts)
        self.configuration.load_cert_chain(certificate, privateKey)
        self.configuration.load_invalid_cert_chain(invalidCertificate)
        self.configuration.secrets_log_file = open(secretsLog, "a")
        self.configuration.cipher_suites = []
         
        # configure the selected cipher suite
        if(cipherSuite == "AES-256-GCM-SHA384"):
            self.configuration.cipher_suites.append(tls.CipherSuite.AES_256_GCM_SHA384)
        elif(cipherSuite == "AES-128-GCM-SHA256"):
            self.configuration.cipher_suites.append(tls.CipherSuite.AES_128_GCM_SHA256)
        elif(cipherSuite == "CHACHA20-POLY1305-SHA256"):
            self.configuration.cipher_suites.append(tls.CipherSuite.CHACHA20_POLY1305_SHA256)
        else:
            self.configuration.cipher_suites = None
            
        if(quicLog):
            self.configuration.quic_logger = QuicFileLogger(quicLog)

        # quic protocol & transport
        self.protocol = None
        self.transport = None

        # server host and port
        self.target = targetServer
        self.targetHost = targetHost
        self.targetPort = targetPort
        self.targetAddr = None
        
        # socket
        self.sock = None
        self.socketCompleted = False

        # localport to bind
        self.localHost = "::"
        self.localPort = localPort
        
        # quic connection
        self.quicVersion = quicVersion
        self.connection = None
        self.firstPacket = True
        self.retryPacket = False
        self.serverMaxITO = 5.0 #3.0
        self.writeNCID = False
        self.isLostResponseBefore = False
        self.normalWaitTime = 0.1 #0.15 for kwik # 0.1 for aioquic #0.5 # 0.035/0.04 # 0.4 or 0.5 for macbook (0.2 for testing aioquic in Uni machine)
        #self.secondWaitTime = 0.15 
        self.shortTimeout = shortTimeout
        self.longTimeout = longTimeout
        
        self.lostWaitTime = 1.0 # 1.2 for macbook?
        self.isIncludeRetryToken = False
        self.afterIncludeRetryToken = False
        self.isGetShortTimeout = isGetShortTimeout
        self.sessionTicket = sessionTicket
        self.ableToDisconnect = False
        self.ableSend0RTTState = Send0rttState.NOT_READY

        # use to track back the response once the handshake is done
        self.zeroRTTInput = []

        # for Quinn to ensure that the New_Connection_ID frame is sent to the Learner after Handshake_Done
        # this prevent non-deterministic where sometimes Quinn server sends New_Connection_ID before Handshake Done and sometimes after Handshake_Done
        self.temp_response_list = []

        # get session ticket for 0-RTT
        if(sessionTicket):
            try:
                with open(sessionTicket, "rb") as fp:
                    self.configuration.session_ticket = pickle.load(fp)
            except Exception as e:
                pass

        # event loop
        self.loop = asyncio.get_event_loop()


    async def start(self):
        print("Starting Mapper...")
        try:
            # loop up target IP & port
            infos = socket.getaddrinfo(self.targetHost, self.targetPort, type=socket.SOCK_DGRAM)
            self.targetAddr = infos[0][4]
            if len(self.targetAddr) == 2:
                self.targetAddr = ("::ffff:" + self.targetAddr[0], self.targetAddr[1], 0, 0)

            # create quic connection object, prepare quic connection
            if(self.sessionTicket):
                self.connection = QuicConnection(configuration=self.configuration, session_ticket_handler=self.save_session_ticket, 
                                                 set_able_send_0rtt_state_cb=self.setAbleSend0rttState)
            else:
                self.connection = QuicConnection(configuration=self.configuration)

            # added here so that the connection know what target we fuzzing now
            self.connection.target = self.target

            # added here so that the connection know to time the short timeout
            if(self.isGetShortTimeout):
                self.connection.isGetShortTimeout = True

            # explicitly enable IPv4/IPv6 dual stack
            self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

            # create and bind socket
            print("    Binding socket...")
            try:
                self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                self.sock.bind((self.localHost, self.localPort, 0, 0))
                self.socketCompleted = True
                print("    Socket bind done.")
            except Exception as e:
                print(e)
            finally:
                if not self.socketCompleted:
                    prRed("    Socket bind failed.")
                    self.sock.close()

            # create datagram endpoint
            # no stream handler for now
            self.transport, self.protocol = await self.loop.create_datagram_endpoint(
            lambda: QuicConnectionProtocol(self.connection, stream_handler=None),
            sock=self.sock,
            )

            # cast quic protocol
            self.protocol = cast(QuicConnectionProtocol, self.protocol)
            # setting up network path and application version

            print("    Initializing Network path & application version...")
            self.connection.setupNetworkPathAndVersion(self.targetAddr, self.quicVersion)
            print("    Successfully initialized network path & application version.")

            print("Starting done.")
        except Exception as e:
            prRed("Starting failed.")
            print(e)

    # set up peer's connection id and idle timeout before first packet is send
    async def initialize(self):
        if self.firstPacket or self.retryPacket:
            if(self.firstPacket):
                print("Initializing peer's connection id & idle timeout...")
            else:
                print("    Reinitializing peer's connection id & idle timeout...")

            try:
                self.connection.initialize(self.loop.time())

                if(self.firstPacket):
                    print("Successfully initialized peer's connection id & idle timeout.")
                else:
                    print("    Successfully reinitialized peer's connection id & idle timeout.")
            except Exception as e:
                if(self.firstPacket):
                    prRed("Failed to initialize peer's connection id & idle timeout.")
                else:
                    prRed("    Failed to initialize peer's connection id & idle timeout.")
                
                print(e)

            self.firstPacket = False
            self.retryPacket = False

    # for 0-RTT (save the session ticket)
    def save_session_ticket(self, ticket: tls.SessionTicket) -> None:
        """
        Callback which is invoked by the TLS engine when a new session ticket
        is received.
        """
        if self.sessionTicket:
            with open(self.sessionTicket, "wb") as fp:
                pickle.dump(ticket, fp)
            
            self.ableToDisconnect = True
            self.setAbleSend0rttState(tls.State.CLIENT_PROCESSED_SESSION_TICKET)

    # for 0-RTT let the mapper know when it can start/stop sending 0-RTT packets
    # start sending after mapper send Client Hello
    # stop sending after mapper received HandshakeDone
    def setAbleSend0rttState(self, tlsState: tls.State) -> None:
        if(tlsState == tls.State.CLIENT_EXPECT_SERVER_HELLO and self.ableSend0RTTState == Send0rttState.NOT_READY):
            self.ableSend0RTTState = Send0rttState.READY
        elif(tlsState == tls.State.CLIENT_PROCESSED_SESSION_TICKET and self.ableSend0RTTState == Send0rttState.READY):
            self.ableSend0RTTState = Send0rttState.TOO_LATE


    # include retry token in initial packet later
    async def includeRetryToken(self, isNewConnection):
        print("    Initializing retry token.")

        if(self.connection.receivedToken != b""):
            if(not self.isIncludeRetryToken):
                try:
                    if(isNewConnection):
                        self.connection.initialize(self.loop.time()) # solve iCH-ack-but-no-process-bug (iCH offset error)
                    
                    self.connection.includeRetryToken()
                    self.isIncludeRetryToken = True

                    print("    Successfully initialized retry token.")
                except Exception as e:
                    prRed("    Failed to initialize retry token.")
                    prRed("     " + str(e))
            else:
                print("    Retry token has been initialized before.")
        else:
            print("    There is no token available.")

    # include invalid (changing the last byte) retry token in initial packet later
    async def includeInvalidRetryToken(self, isNewConnection):
        print("    Initializing invalid retry token.")

        if(self.connection.receivedToken != b""):
            if(not self.isIncludeRetryToken):
                try:
                    if(isNewConnection):
                        self.connection.initialize(self.loop.time()) # solve iCH-ack-but-no-process-bug (iCH offset error)
                    
                    self.connection.includeInvalidRetryToken()
                    self.isIncludeRetryToken = True

                    print("    Successfully initialized invalid retry token.")
                except Exception as e:
                    prRed("    Failed to initialize invalid retry token.")
                    prRed("     " + str(e))
            else:
                print("    Invalid Retry token has been initialized before.")
        else:
            print("    There is no token available.")

    # change the packet's Destination Connection ID field
    async def changeDestinationConnectionID(self, isOriDestConID):
        if(isOriDestConID):
            print("    Changing DCID to server's original DCID.")
        else:
            print("    Changing DCID to server's initial SCID.")

        try:
            self.connection.changeDestinationConnectionID(isOriDestConID)
            print("    Successfully change the Destination Connection ID.")
        except Exception as e:
            prRed("    Failed to change the Destination Connection ID.")
            prRed("     " + str(e))

    # configure the mapper to add/remove padding for the subsequence Initial packets
    async def configureInitialPacketsPadding(self, isAddPadding):
        if(isAddPadding):
            print("    Adding padding to subsequence Initial packets.")
        else:
            print("    Removing padding from subsequence Initial packets.")
        
        try:
            self.connection.configureInitialPacketsPadding(isAddPadding)
            print("    Successfully configured.")
        except Exception as e:
            prRed("    Failed to configure.")
            prRed("     " + str(e))

    # exclude retry token in initial packet later
    async def excludeRetryToken(self):
        try:
            self.connection.excludeRetryToken()
        except Exception as e:
            prRed(e)

    # Initial packet with empty payload
    async def iEmptyPayload(self):
        print("    Sending INITIAL-emptyPayload...")
        try:
            self.connection.emptyPayloadPacket(sendEpochType = tls.Epoch.INITIAL)
            self.protocol.transmit()
            self.connection.resetMalformedPacket()
            prGreen("    INITIAL-emptyPayload sent.")
        except Exception as e:
            prRed("    INITIAL-emptyPayload failed.")
            prRed("     " + str(e))
    
    # Initial packet with unexpected frame type (0xff type)
    async def iUnexpectedFrameType(self):
        print("    Sending INITIAL-unexpectedFrameType...")
        try:
            self.connection.unexpectedFrameTypePacket(sendEpochType = tls.Epoch.INITIAL)
            self.protocol.transmit()
            self.connection.resetMalformedPacket()
            prGreen("    INITIAL-unexpectedFrameType.")
        except Exception as e:
            prRed("    INITIAL-unexpectedFrameType.")
            prRed("     " + str(e))

    #original iClientHello
    # send Initial packet - clientHello
    async def iClientHello(self):
        print("    Sending INITIAL-clientHello...")
        try:
            #self.connection.initialize(self.loop.time()) # try
            self.connection.clientHello()
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    INITIAL-clientHello sent.")
        except Exception as e:
            prRed("    INITIAL-clientHello failed.")
            prRed("     " + str(e))

    # send Initial packet - clientHello that will respond iSH with an invalid (no padding) ack
    async def iClientHelloInvalidInitialAck(self, cipherSuite):
        print("    Sending INITIAL-clientHello...")
        try:
            self.connection.padInitialACK = 0
            self.connection.clientHello(cipherSuite)
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    INITIAL-clientHello sent.")
        except Exception as e:
            prRed("    INITIAL-clientHello failed.")
            prRed("     " + str(e))

    # send Initial packet - clientHello that will respond iSH with a valid (padding) ack
    async def iClientHelloValidInitialAck(self, cipherSuite):
        print("    Sending INITIAL-clientHello...")
        try:
            self.connection.padInitialACK = 1
            self.connection.clientHello(cipherSuite)
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    INITIAL-clientHello sent.")
        except Exception as e:
            prRed("    INITIAL-clientHello failed.")
            prRed("     " + str(e))

    # send INITIAL packet - ping()
    # send ping to server with before handshake complete
    # no padding will still have one padding to ensure sufficient packet size/length
    async def iProbe(self):
        print("    Sending INITIAL-ping...")
        try:
            self.connection.probe(sendEpochType = tls.Epoch.INITIAL)
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    INITIAL-ping sent.")
        except Exception as e:
            prRed("    INITIAL-ping failed.")
            prRed("     " + str(e))

    # send INITIAL packet - connectionClose()
    async def iConnectionClose(self):
        print("    Sending INITIAL-connectionClose...")
        try:
            self.connection.close(sendEpochType = tls.Epoch.INITIAL)
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    INITIAL-connectionClose sent.")
        except Exception as e:
            prRed("    INITIAL-connectionClose failed.")
            prRed("     " + str(e))

    # 0-RTT packet - ping()
    async def zeroPing(self):
        print("    Sending ZeroRTT-ping...")
        try:
            self.connection.probe(sendEpochType = tls.Epoch.ZERO_RTT)
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    ZeroRTT-ping sent.")
        except Exception as e:
            prRed("    ZeroRTT-ping failed.")
            prRed("     " + str(e))

    # 0-RTT packet - ping()
    async def zeroConnectionClose(self):
        print("    Sending ZeroRTT-connectionClose...")
        try:
            self.connection.close(sendEpochType = tls.Epoch.ZERO_RTT)
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    ZeroRTT-connectionClose sent.")
        except Exception as e:
            prRed("    ZeroRTT-connectionClose sent.")
            prRed("     " + str(e))

    # 0-RTT packet - FINISHED()
    async def zeroFinished(self):
        print("    Sending ZeroRTT-FINISHED...")
        try:
            self.connection.sendFinished(epoch = tls.Epoch.ZERO_RTT)
            self.protocol._process_events()
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    ZeroRTT-FINISHED sent.")
        except Exception as e:
            prRed("    ZeroRTT-FINISHED failed.")
            prRed("     " + str(e))

    # 0-RTT packet with empty payload
    async def zeroEmptyPayload(self):
        print("    Sending ZeroRTT-EmptyPayload...")
        try:
            self.connection.emptyPayloadPacket(sendEpochType = tls.Epoch.ZERO_RTT)
            self.protocol.transmit()
            self.connection.resetMalformedPacket()
            prGreen("    ZeroRTT-EmptyPayload sent.")
        except Exception as e:
            prRed("    ZeroRTT-EmptyPayload failed.")
            prRed("     " + str(e))

    # 0-RTT packet with unexpected frame type (0xff type)
    async def zeroUnexpectedFrameType(self):
        print("    Sending ZeroRTT-unexpectedFrameType...")
        try:
            self.connection.unexpectedFrameTypePacket(sendEpochType = tls.Epoch.ZERO_RTT)
            self.protocol.transmit()
            self.connection.resetMalformedPacket()
            prGreen("    ZeroRTT-unexpectedFrameType.")
        except Exception as e:
            prRed("    ZeroRTT-unexpectedFrameType.")
            prRed("     " + str(e))

    # 0-RTT packet with malformed ACK
    async def zeroAck(self):
        print("    Sending ZeroRTT-ACK...")
        try:
            self.connection.ackFrame(sendEpochType=tls.Epoch.ZERO_RTT)
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    ZeroRTT-ACK.")
        except Exception as e:
            prRed("    ZeroRTT-ACK.")
            prRed("     " + str(e))

    # Handshake packet with empty payload
    async def hEmptyPayload(self):
        print("    Sending HANDSHAKE-emptyPayload...")
        try:
            self.connection.emptyPayloadPacket(sendEpochType = tls.Epoch.HANDSHAKE)
            self.protocol.transmit()
            self.connection.resetMalformedPacket()
            prGreen("    HANDSHAKE-emptyPayload sent.")
        except Exception as e:
            prRed("    HANDSHAKE-emptyPayload failed.")
            prRed("     " + str(e))

    # Handshake packet with unexpected frame type (0xff type)
    async def hUnexpectedFrameType(self):
        print("    Sending HANDSHAKE-unexpectedFrameType...")
        try:
            self.connection.unexpectedFrameTypePacket(sendEpochType = tls.Epoch.HANDSHAKE)
            self.protocol.transmit()
            self.connection.resetMalformedPacket()
            prGreen("    HANDSHAKE-unexpectedFrameType.")
        except Exception as e:
            prRed("    HANDSHAKE-unexpectedFrameType.")
            prRed("     " + str(e))

    # send HANDSHAKE packet - ping()
    # send ping to server with before handshake complete
    async def hProbe(self):
        print("    Sending HANDSHAKE-ping...")
        try:
            self.connection.probe(sendEpochType = tls.Epoch.HANDSHAKE)
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    HANDSHAKE-ping sent.")
        except Exception as e:
            prRed("    HANDSHAKE-ping failed.")
            prRed("     " + str(e))

    # send HANDSHAKE packet - connectionClose()
    async def hConnectionClose(self):
        print("    Sending HANDSHAKE-connectionClose...")
        try:
            self.connection.close(sendEpochType = tls.Epoch.HANDSHAKE)
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    HANDSHAKE-connectionClose sent.")
        except Exception as e:
            prRed("    HANDSHAKE-connectionClose failed.")
            prRed("     " + str(e))

    # send HANDSHAKE packet - CERTIFICATE()
    async def hCertificate(self):
        print("    Sending HANDSHAKE-CERTIFICATE...")
        try:
            self.connection.sendValidClientCertificate()
            self.protocol._process_events()
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    HANDSHAKE-CERTIFICATE sent.")
        except Exception as e:
            prRed("    HANDSHAKE-CERTIFICATE failed.")
            prRed("     " + str(e))

    # send HANDSHAKE packet - EMPTY_CERTIFICATE()
    async def hEmptyCertificate(self):
        print("    Sending HANDSHAKE-EMPTY_CERTIFICATE...")
        try:
            self.connection.sendEmptyClientCertificate()
            self.protocol._process_events()
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    HANDSHAKE-EMPTY_CERTIFICATE sent.")
        except Exception as e:
            prRed("    HANDSHAKE-EMPTY_CERTIFICATE failed.")
            prRed("     " + str(e))

    # send HANDSHAKE packet - invalid CERTIFICATE()
    # send the certificate that is not matched with public key
    async def hInvalidCertificate(self):
        print("    Sending HANDSHAKE-INVALID_CERTIFICATE...")
        try:
            self.connection.sendInvalidClientCertificate()
            self.protocol._process_events()
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    HANDSHAKE-INVALID_CERTIFICATE sent.")
        except Exception as e:
            prRed("    HANDSHAKE-INVALID_CERTIFICATE failed.")
            prRed("     " + str(e))

    # send HANDSHAKE packet - CERTIFICATE_VERIFY()
    async def hCertificateVerify(self):
        print("    Sending HANDSHAKE-CERTIFICATE_VERIFY...")
        try:
            self.connection.sendClientCertificateVerify()
            self.protocol._process_events()
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    HANDSHAKE-CERTIFICATE_VERIFY sent.")
        except Exception as e:
            prRed("    HANDSHAKE-CERTIFICATE_VERIFY failed.")
            prRed("     " + str(e))

    # send HANDSHAKE packet - FINISHED()
    async def hFinished(self):
        print("    Sending HANDSHAKE-FINISHED...")
        try:
            self.connection.sendFinished()
            self.protocol._process_events()
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    HANDSHAKE-FINISHED sent.")
        except Exception as e:
            prRed("    HANDSHAKE-FINISHED failed.")
            prRed("     " + str(e))

    # send 1-RTT packet - ping()
    # send ping to server after the handshake is complete
    async def oneProbe(self):
        print("    Sending 1-RTT-ping...")
        try:
            self.connection.probe(sendEpochType = tls.Epoch.ONE_RTT)
            self.protocol.transmit()
            self.connection.resetSendEpochType()
            prGreen("    1-RTT-ping sent.")
        except Exception as e:
            prRed("    1-RTT-ping failed.")
            prRed("     " + str(e))

    # send valid short header packet - NCID()
    async def sValidNewConnectionID(self):
        # only send the valid new connection ID when finished is sent
        if(self.connection._handshake_complete and not self.writeNCID):
            print("    Sending valid new connection IDs...")
            try:
                self.connection.sendValidNCID()
                self.protocol.transmit()
                self.writeNCID = True

                prGreen("    Valid new connection IDs sent.")
            except Exception as e:
                prRed("    Valid new connection IDs failed to send.")
                prRed("     " + str(e))
        else:
            # cannot send NCID because handshake not yet complete,
            # cannot write NCID in write_application
            self.connection.mapperError.append("Write NCID ERROR")
            print("    Unable to send valid NCID, skipping...")

    # send invalid short header packet - NCID()
    async def sInvalidNewConnectionID(self):
        # only send the invalid new connection ID when finished is sent
        if(self.connection._handshake_complete and not self.writeNCID):
            print("    Sending invalid new connection IDs...")
            try:
                self.connection.sendInvalidNCID()
                self.protocol.transmit()
                self.writeNCID = True

                prGreen("    Invalid new connection IDs sent.")
            except Exception as e:
                prRed("    Invalid new connection IDs failed to send.")
                prRed("     " + str(e))
        else:
            # cannot send NCID because handshake not yet complete,
            # cannot write NCID in write_application
            self.connection.mapperError.append("Write NCID ERROR")
            print("    Unable to send invalid NCID, skipping...")
    
    # send HANDSHAKE packet - connectionClose()
    async def nConnectionClose(self):
        print("    Sending Normal-connectionClose...")
        try:
            self.connection.close(sendEpochType = None)
            self.protocol.transmit()
            prGreen("    Normal-connectionClose sent.")
        except Exception as e:
            prRed("    Normal-connectionClose failed.")
            prRed("     " + str(e))

    # ping the server to check if the connection is still alive or not
    # set sendEpochType to None 
    # so that the mapper will send the packet in current packet space
    async def checkServerClose(self, isCheck2Conn=False):
        if(MapperError.NOT_ABLE_TO_WRITE_CONNECTION_CLOSE not in self.connection.mapperError):
            if(not isCheck2Conn):
                print("    Checking if server has closed...")
            try:
                self.connection.probe(sendEpochType = None)
                self.protocol.transmit()
                if(not isCheck2Conn):
                    prGreen("    Check-ping sent.")
            except Exception as e:
                prRed("    Check-ping failed.")
                prRed("     " + str(e))
    
    # wait for server's maximum idle timeout
    async def waitUntilServerMaxITO(self):
        print("    Waiting until server max idle timeout...")
        try:
            await asyncio.sleep(self.serverMaxITO)
            prGreen("    Wait ended.")
        except Exception as e:
            prRed("    Wait failed.")
            prRed("     " + str(e))

    # protocol drops all the packets
    async def lostResponse(self):
        self.protocol.isLostResponse = True

    # protocol accepts all the packets
    async def acceptResponse(self):
        self.protocol.isLostResponse = False

    # create a invalid destination connection ID
    # store in invalidDestConIDList
    # overwrite the value in self.connection._peer_cid
    #async def createAndUseInvalidDestConID(self):
    #    print("    Creating a new invalid destination connection id...")
    #    print("    Previous destination connection id: " + str(self.connection._peer_cid.cid))
    #    self.connection.createAndUseInvalidDestConID()
    #    print("    New destination connection id:      " + str(self.connection._peer_cid.cid))

    # change the to a invalid destination connection ID stored in the invalidDestConIDList
    #async def changeDestConID(self, conIDIndex):
    #    print("    Previous destination connection id: " + str(self.connection._peer_cid.cid))
    #    self.connection.changeDestConID(conIDIndex)
    #    print("    Current destination connection id:  " + str(self.connection._peer_cid.cid))
        
    def sortNewSessionTicket(output):
        return(output != Output.NEW_SESSION_TICKET, output)

    # get server response and print them
    async def getResponse(self, input, isLostWait):

        # if normal wait time then shorter wait time
        # if lost packet then longer wait time to ensure the retrasmitted packets are received
        if(not isLostWait):
            await asyncio.sleep(self.normalWaitTime) # uni machine
            #self.protocol.transmit()
            #await asyncio.sleep(self.secondWaitTime)
        else:
            print("    Waiting lost response...")
            await asyncio.sleep(self.lostWaitTime)

        # list to store all the response from the server
        responseList = []

        # add this variable to keep track and make sure there is only one retry for ConClose input
        # bcs ConClose msg (which will send 2 inputs including ConClose + probe)
        oneRetry = False

        if(self.connection.peerResponse):
            isFirstPeerResponse = 1
            #print(self.connection.peerResponse)
            
            # do this to solve non-deterministic in Kwik
            # the server will send 'PingACK,initSvrHello ' in different order or missing PingACK in the response
            if(self.target == Server.KWIK and "PING.ACKED" in self.connection.peerResponse and tls.HandshakeType.SERVER_HELLO in self.connection.peerResponse):
                while("PING.ACKED" in self.connection.peerResponse):
                    self.connection.peerResponse.remove("PING.ACKED")

                #self.connection.peerResponse.sort()

            for response in self.connection.peerResponse:
                abResponse = str(response).split(" ")[0]

                if(abResponse == "PING.ACKED"  and self.target != Server.MSQUIC): #and self.target != Server.QUICLY
                    # dont consider quicly because of its handshake timeout
                    # If server acked check ping when CC is sent 
                    # Then connection still active at the server side
                    # Reset the close event
                    if(Input.INITIAL_CONNECTION_CLOSE in input or Input.HANDSHAKE_CONNECTION_CLOSE in input
                       or Input.ZERORTT_CONNECTION_CLOSE in input
                        or Input.NORMAL_CONNECTION_CLOSE in input or input == Input.WAIT_SERVER_IDLE_TIMEOUT):
                        if(input != Input.WAIT_SERVER_IDLE_TIMEOUT):
                            self.connection.resetCloseEvent()

                        abResponse = Output.CONNETION_ACTIVE # Connection Active
                        response = "<Connection Active>"
                    elif(Input.INITIAL_PING in input or Input.HANDSHAKE_PING in input or Input.ONE_RTT_PING in input):
                        abResponse = Output.PING_ACKED   # normal Ping Acked
                    elif(Input.ZERORTT_PING in self.zeroRTTInput):
                        abResponse = Output.PING_ACKED   # normal Ping Acked
                        self.zeroRTTInput.remove(Input.ZERORTT_PING)
                    else:
                        abResponse = ""
                elif(abResponse == "HandshakeType.SERVER_HELLO"):
                    abResponse = Output.INITIAL_SERVER_HELLO # initial Server Hello
                elif(abResponse == "HANDSHAKE_DONE"):
                    abResponse = Output.HANDSHAKE_DONE  # handshake Handshake Done
                elif(abResponse == "HandshakeType.ENCRYPTED_EXTENSIONS"):
                    abResponse = Output.HANDSHAKE_ENCRYPTED_EXTENSIONS  # handshake Encrypted Extensions
                elif(abResponse == "HandshakeType.CERTIFICATE_REQUEST"):
                    abResponse = Output.HANDSHAKE_CERTIFICATE_REQUEST   # handshake Certificate Request
                elif(abResponse == "HandshakeType.CERTIFICATE"):
                    abResponse = Output.HANDSHAKE_CERTIFICATE   # handshake Certificate
                elif(abResponse == "HandshakeType.CERTIFICATE_VERIFY"):
                    abResponse = Output.HANDSHAKE_CERTIFICATE_VERIFY  # handshake Certificate Verify
                elif(abResponse == "HandshakeType.FINISHED"):
                    abResponse = Output.HANDSHAKE_FINISHED   # handshake Finished
                elif(abResponse == "HandshakeType.NEW_SESSION_TICKET"):
                    if(self.target != Server.QUICHE4J):
                        abResponse = Output.NEW_SESSION_TICKET   # NEW_SESSION_TICKET frame
                    else:
                        abResponse = ""
                elif(abResponse == "NEW_TOKEN"):
                    if(self.target != Server.QUICLY):
                        abResponse = Output.NEW_TOKEN   # NEW_TOKEN frame
                    else:
                        abResponse = ""
                elif(abResponse == "NEW_CONNECTION_ID"):
                    # temporary store VldNewConID for Quinn
                    if((self.target == Server.QUINN or self.target == Server.LSQUIC) and not self.connection._handshake_confirmed):
                        self.temp_response_list.append(response)
                        abResponse = ""
                    else:
                        abResponse = Output.VALID_NEW_CONNECTION_ID    # short header New Connection ID
                elif(abResponse == "RETRY"):
                    if(self.target == Server.MSQUIC): #or self.target == Server.QUANT):
                        if(not self.retryPacket):
                            abResponse = Output.RETRY # retry packet
                        else:
                            abResponse = ""
                    # added this line to prevent the mapper with connection that is still active has a CloseEvent after sending a ConClose msg
                    elif(Input.INITIAL_CONNECTION_CLOSE in input or Input.HANDSHAKE_CONNECTION_CLOSE in input or Input.ZERORTT_CONNECTION_CLOSE in input
                        or Input.NORMAL_CONNECTION_CLOSE in input and self.target != Server.NGTCP2 or self.target != Server.QUINN):
                            self.connection.resetCloseEvent()
                        
                            if(not oneRetry):
                                abResponse = Output.RETRY # retry packet
                                oneRetry = True
                            else:
                                abResponse = ""
                    else:
                        abResponse = Output.RETRY # retry packet
                    
                    # set this varaible so that the mapper know when is the first retry packet received
                    self.retryPacket = True
                elif(abResponse == "ACK"):
                    abResponse = Output.NORMAL_ACK
                elif(abResponse == "CONNECTION_CLOSE"):
                    abResponse = Output.NORMAL_CONNECTION_CLOSE
                    self.connection.closeMapperConnection(now=self.loop.time()) # close mapper connection (prevent non-deterministic)
                elif(abResponse == "Ping"):
                    abResponse = "nP"
                elif(abResponse == "VERSION_NEGOTIATION"):
                    abResponse = Output.VERSION_NEGOTIATION
                else:
                    prRed("    Parser Error: Unable to parse the server's response: " + abResponse)
                    abResponse = ""

                
                
                # only print/send the output if it is not ACK and not nothing
                if(abResponse != Output.NORMAL_ACK and abResponse != ""):
                    if(isFirstPeerResponse == 1):
                        isFirstPeerResponse = 0
                        print("    -----Server's response: -----")

                    responseList.append(abResponse)
                    print("    " + str(response))

                    # Specially for Quinn bcs it sometimes send New_Connection_ID before Hanshake_Done and sometimes after 
                    if((self.target == Server.QUINN or self.target == Server.LSQUIC) and abResponse == Output.HANDSHAKE_DONE and self.temp_response_list):
                        for response in self.temp_response_list:
                            if(str(response).split(" ")[0] == "NEW_CONNECTION_ID"):
                                responseList.append(Output.VALID_NEW_CONNECTION_ID)
                                print("    " + str(response))
                        
                        self.temp_response_list.clear()

        if(not self.connection.peerResponse and not self.connection.mapperError 
           or self.target == Server.MSQUIC ):
            # If server does not acked check ping or send back any response, 
            # Then connection is closed at server side
            # Close the mapper side connection
            if(Input.INITIAL_CONNECTION_CLOSE in input or Input.HANDSHAKE_CONNECTION_CLOSE in input
               or Input.ZERORTT_CONNECTION_CLOSE in input 
               or Input.NORMAL_CONNECTION_CLOSE in input or input == Input.WAIT_SERVER_IDLE_TIMEOUT):
                self.connection.closeMapperConnection(now=self.loop.time())
                responseList.append(Output.CONNECTION_CLOSED)

                print("    <Connection Closed>")
            else:
                responseList.append("")

        if(self.connection.closingState):
            print("    -----Mapper's state: -----")
            for state in self.connection.closingState:
                print("    " + str(state))

        # reset some values in self.connection
        self.connection.clearLists()
        self.connection.resetPadInitialACK()

        print()

        # sort the list to prevent non-deterministic
        if(Output.VALID_NEW_CONNECTION_ID in responseList and Output.NEW_SESSION_TICKET in responseList):
            responseList = sorted(responseList, key=lambda x: x == Output.NEW_SESSION_TICKET)

        # print(responseList)

        return responseList

# configure Mapper          
def startConfigureMapper(args):
    print('Configuring Mapper...')
    try:
        # path to stored certificate authority certs
        caCerts = args.caCert
        # path to store secret keys to decrypt in wireshark
        secretsLog = args.secrets
        # path of directory to store the log files
        quicLog = args.log
        
        # key & certs
        certificate = args.certificate
        privateKey = args.privateKey
        invalidCertificate = args.invalidCertificate

        # cipher suite
        cipherSuite = args.cipher

        # session ticket file
        sessionTicket = args.sessionTicket

        # current dictionary used for fuzzing
        inputDictionary = args.input

        # ip and port of the server
        targetServer = args.server
        targetHost = "localhost"
        targetPort = int(args.targetPort)
        # local port to bind
        localPort = int(args.port)

        isGetShortTimeout = False

        # quic version
        quicVersion = ""

        # alpn protocols
        aioAlpn = H0_ALPN #H3_ALPN # aioquic
        picoAlpn = ["h3"]          # picoquic, ngtcp2
        ngtcp2Alpn = ["h3"]
        kwikAlpn = ["hq-29", "hq-30", "hq-interop", "hq-32", "hq-31"]
        quinnAlpn = ["hq-29"]
        msquicAlpn = ["hq-29", "hq-30", "hq-interop", "hq-32", "hq-31"]
        quicheAlpn = ["hq-29", "hq-30", "hq-interop", "hq-32", "hq-31", "h3", ]
        allAlpn = ["hq-29", "hq-30", "hq-interop", "hq-32", "hq-31", "h3", "h3-29", "h3-28", "h3-27"]

        alpnProtocols = allAlpn

        # add here for new server
        if(targetServer == Server.AIOQUIC):
            alpnProtocols = aioAlpn 
            shortTimeout = Server.AIOQUIC_SHORT
            longTimeout = Server.AIOQUIC_LONG
        elif(targetServer == Server.GOOGLEQUIC):
            alpnProtocols = allAlpn
            shortTimeout = Server.GOOGLEQUIC_SHORT
            longTimeout = Server.GOOGLEQUIC_LONG
        elif(targetServer == Server.PICOQUIC):
            alpnProtocols = picoAlpn
            shortTimeout = Server.PICOQUIC_SHORT
            longTimeout = Server.PICOQUIC_LONG
        elif(targetServer == Server.NGTCP2):
            alpnProtocols = ngtcp2Alpn
            shortTimeout = Server.NGTCP2_SHORT
            longTimeout = Server.NGTCP2_LONG
        elif(targetServer == Server.QUINN):
            alpnProtocols = quinnAlpn
            shortTimeout = Server.QUINN_SHORT
            longTimeout = Server.QUINN_LONG
        elif(targetServer == Server.KWIK):
            alpnProtocols = kwikAlpn
            shortTimeout = Server.KWIK_SHORT
            longTimeout = Server.KWIK_LONG
        elif(targetServer == Server.MSQUIC):
            alpnProtocols = msquicAlpn
            shortTimeout = Server.MSQUIC_SHORT
            longTimeout = Server.MSQUIC_LONG
        elif(targetServer == Server.QUICHE):
            alpnProtocols = quicheAlpn
            shortTimeout = Server.QUICHE_SHORT
            longTimeout = Server.QUICHE_LONG
        elif(targetServer == Server.XQUIC):
            alpnProtocols = allAlpn
            shortTimeout = Server.XQUIC_SHORT
            longTimeout = Server.XQUIC_LONG
        elif(targetServer == Server.QUICLY):
            alpnProtocols = allAlpn
            shortTimeout = Server.QUICLY_SHORT
            longTimeout = Server.QUICLY_LONG
        elif(targetServer == Server.QUANT):
            alpnProtocols = allAlpn
            shortTimeout = Server.QUANT_SHORT
            longTimeout = Server.QUANT_LONG
        elif(targetServer == Server.S2NQUIC):
            alpnProtocols = allAlpn
            if('WR' in inputDictionary):
                shortTimeout = Server.S2NQUIC_SHORT_RETRY
                longTimeout = Server.S2NQUIC_LONG_RETRY
            else:
                shortTimeout = Server.S2NQUIC_SHORT
                longTimeout = Server.S2NQUIC_LONG
        elif(targetServer == Server.NEQO):
            alpnProtocols = allAlpn
            if('WR' in inputDictionary):
                shortTimeout = Server.NEQO_SHORT_RETRY
                longTimeout = Server.NEQO_LONG_RETRY
            else:
                shortTimeout = Server.NEQO_SHORT
                longTimeout = Server.NEQO_LONG
        elif(targetServer == Server.QUICGO):
            alpnProtocols = allAlpn
            shortTimeout = Server.QUICGO_SHORT
            longTimeout = Server.QUICGO_LONG
        elif(targetServer == Server.LSQUIC):
            alpnProtocols = allAlpn
            shortTimeout = Server.LSQUIC_SHORT
            longTimeout = Server.LSQUIC_LONG
        elif(targetServer == Server.PQUIC):
            quicVersion = QuicProtocolVersion.DRAFT_29
            alpnProtocols = allAlpn
            shortTimeout = Server.PQUIC_SHORT
            longTimeout = Server.PQUIC_LONG
        elif(targetServer == Server.QUIWI):
            alpnProtocols = allAlpn
            shortTimeout = Server.QUIWI_SHORT
            longTimeout = Server.QUIWI_LONG
        elif(targetServer == Server.QUICHE4J):
            quicVersion = QuicProtocolVersion.DRAFT_29
            alpnProtocols = allAlpn
            shortTimeout = Server.QUICHE4J_SHORT
            longTimeout = Server.QUICHE4J_LONG
        elif(targetServer == Server.MVFST):
            alpnProtocols = allAlpn
            shortTimeout = Server.MVFST_SHORT
            longTimeout = Server.MVFST_LONG
        
        # for getShortTimeout
        else:
            isGetShortTimeout = True
            alpnProtocols = allAlpn
            shortTimeout = None
            longTimeout = None

        '''logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        level=logging.DEBUG,
        )'''

        # setting up the configurations
        mapper = Mapper(alpnProtocols, caCerts, secretsLog, quicLog, targetServer, targetHost, targetPort, localPort, 
                        certificate, privateKey, invalidCertificate, shortTimeout, longTimeout, cipherSuite, quicVersion, isGetShortTimeout,
                        sessionTicket)
        print("Configuration done.")
        
        return mapper
    except Exception as e:
        prRed("Configuration failed.")
        print(e)

# fuzz by sequence at once
async def fuzzSeq(inSequence):
    print("Start fuzzing...")

    mapper = startConfigureMapper(args)
    await mapper.start()
    await mapper.initialize()
    
    # use to store the mapper of the first connection
    mapper1 = None

    for input in inSequence:
        responseList = await fuzzIn(mapper, input)
        if(responseList == Input.DISCONNECT):
            #mapper1 = mapper
            #args.port = str(int(args.port) + 1)
            mapper.transport.close()
            await asyncio.sleep(0)
            print("Starting a second connection...")
            mapper = startConfigureMapper(args)
            await mapper.start()
            await mapper.initialize()
    
    # test whether the mapper in the first connection still alive
    if(mapper1 != None):
        #await mapper1.nConnectionClose()
        await asyncio.sleep(0.2)
        mapper1.connection.clearLists()
        mapper.connection.clearLists()
        print("Checking the status of the connections...")
        await mapper1.checkServerClose(isCheck2Conn=True)
        await mapper.checkServerClose(isCheck2Conn=True)
        await asyncio.sleep(0.2)

        if(mapper1.connection.peerResponse):
            print("1st Connection is alive.")
        else:
            print("1st Connection is death.")


        if(mapper.connection.peerResponse):
            print("2nd Connection is alive.")
        else:
            print("2nd Connection is death.")
        
        mapper1.connection.clearLists()
        mapper.connection.clearLists()
        mapper1.transport.close()

    
    # close the transport layer
    mapper.transport.close()
    # remove the session ticket file
    
    if(args.getSessionTicket):
        # remove the session ticket file under 2 conditions:
        # 1) Mapper has not use the session ticket
        # 2) Mapper has establish a new connection and get a new session ticket
        if(mapper.ableSend0RTTState == Send0rttState.READY or mapper.target == Server.KWIK):
            if(os.path.exists(args.sessionTicket)):
                os.remove(args.sessionTicket)
    elif(os.path.exists(args.sessionTicket)):
        # remove the session ticket if --getSessionTicket is not set
        os.remove(args.sessionTicket)

    print("End fuzzing")
    print("_____________________________________________________________")

    # give the mapper sometime to do the job
    await asyncio.sleep(0.2)

# fuzz by input one by one
async def fuzzIn(mapper, input):
    responseList = []
    # this value need to be False if the input did not send anything to the server (only do something on the mapper itself)
    isSendPkt = True

    if(input == Input.WAIT_LOST_RESPONSE and mapper.isLostResponseBefore):
        responseList = await mapper.getResponse(input=input, isLostWait=True)
        mapper.isLostResponseBefore = False
    elif(not mapper.isLostResponseBefore):
        # if lost symbol in abstract input, do not accept the response from the server
        # act that the packet (response) has lost
        if(Input.LOST_SYMBOL in input and not mapper.isLostResponseBefore):
            # set this so protocol will drop all the packets
            await mapper.lostResponse()

        # Stop sending packets when the server and mapper has closed the connection
        # Stop sending Initial packet once changing to Destination Connection ID and Hanshake is confirmed
        # This prevent the server identify the packet as an new incoming connection
        # The remaining input will mark output as "" 
        if(mapper.connection._state not in END_STATES and not (input.startswith(Input.INITIAL_PREFIX) and 
           mapper.connection._peer_cid.cid == mapper.connection._original_destination_connection_id and 
           mapper.connection._handshake_confirmed)):
            if(Input.SHORT_SYMBOL in input):
                if sys.version_info >= (3, 9):
                    # Use removesuffix for Python 3.9 and later
                    input = input.removesuffix(Input.SHORT_SYMBOL)
                else:
                    # Use slicing for Python versions earlier than 3.9
                    if input.endswith(Input.SHORT_SYMBOL):
                        input = input[: -len(Input.SHORT_SYMBOL)]

                mapper.normalWaitTime = mapper.shortTimeout
            elif(Input.LONG_SYMBOL in input):
                if sys.version_info >= (3, 9):
                    # Use removesuffix for Python 3.9 and later
                    input = input.removesuffix(Input.LONG_SYMBOL)
                else:
                    # Use slicing for Python versions earlier than 3.9
                    if input.endswith(Input.LONG_SYMBOL):
                        input = input[: -len(Input.LONG_SYMBOL)]
                mapper.normalWaitTime = mapper.longTimeout
            else:
                mapper.normalWaitTime = mapper.shortTimeout

            # Initial inputs
            if(input.startswith(Input.INITIAL_PREFIX)):
                # start generating input here
                # initial ping packet
                if(input == Input.INITIAL_PING):
                    if(mapper.target != Server.MVFST):
                        await mapper.iProbe()
                    else:
                        isSendPkt = False
                # initial client hello packet
                elif(Input.INITIAL_CLIENT_HELLO in input):
                    cipherSuite = None

                    # get cipher suite (if any)
                    if(Input.CIPHER_SYMBOL in input):
                        cipherSuite = input.split(":")[1]
                        cipherSuite = cipherSuite.replace("-", "_")

                    if(Input.VALID_ACK_SYMBOL in input):
                        await mapper.iClientHelloValidInitialAck(cipherSuite)
                    elif(Input.INVALID_ACK_SYMBOL in input):
                        await mapper.iClientHelloInvalidInitialAck(cipherSuite)
                    else:
                        await mapper.iClientHello()
                elif(input == Input.INITIAL_CONNECTION_CLOSE):
                    # initial connection close packet
                    await mapper.iConnectionClose()
                elif(input == Input.INITIAL_EMPTY_PAYLOAD):
                    await mapper.iEmptyPayload()
                elif(input == Input.INITIAL_UNEXPECTED_FRAME_TYPE):
                    await mapper.iUnexpectedFrameType()
                else:
                    prRed("ERROR: input not defined.")
            
            # 0-RTT inputs
            # only send 0-rtt inputs after the mapper has sent client hello and before the mapper send finished
            # do this because the server may discarded the 0-RTT key after that point causing non-deterministic
            elif(input.startswith(Input.ZERORTT_PREFIX)):
                if(mapper.ableSend0RTTState == Send0rttState.READY):
                    if(input == Input.ZERORTT_PING):
                        if(mapper.target != Server.MVFST and mapper.target != Server.AIOQUIC and mapper.target != Server.KWIK and 
                           mapper.target != Server.PQUIC and mapper.target != Server.QUICHE4J):
                            mapper.zeroRTTInput.append(Input.ZERORTT_PING)
                            await mapper.zeroPing()
                        else:
                            isSendPkt = False
                    elif(input == Input.ZERORTT_CONNECTION_CLOSE):
                        if(mapper.target != Server.PQUIC and mapper.target != Server.QUICHE4J):
                            await mapper.zeroConnectionClose()
                        else:
                            isSendPkt = False
                    elif(input == Input.ZERORTT_FINISHED):
                        if(mapper.target != Server.PQUIC and mapper.target != Server.QUICHE4J):
                            await mapper.zeroFinished()
                        else:
                            isSendPkt = False
                    elif(input == Input.ZERORTT_EMPTY_PAYLOAD):
                        if(mapper.target != Server.PQUIC and mapper.target != Server.QUICHE4J):
                            await mapper.zeroEmptyPayload()
                        else:
                            isSendPkt = False
                    elif(input == Input.ZERORTT_UNEXPECTED_FRAME_TYPE):
                        if(mapper.target != Server.PQUIC and mapper.target != Server.QUICHE4J):
                            await mapper.zeroUnexpectedFrameType()
                        else:
                            isSendPkt = False
                    elif(input == Input.ZERORTT_ACK):
                        if(mapper.target != Server.NEQO and mapper.target != Server.PQUIC and mapper.target != Server.QUICHE4J):
                            await mapper.zeroAck()
                        else:
                            isSendPkt = False
                    else:
                        prRed("ERROR: input not defined.")
                #else:
                    # print("\n    Unable to send 0-RTT packet to prevent non-deterministic on the Learner." )
                    # print("    Skipping " + input + ".\n")
                else:
                    print("\n    Unable to send 0-RTT packet at this point.")
                    print("    Skipping " + input + ".\n")
                    isSendPkt = False
            
            # Handshake inputs
            elif(input.startswith(Input.HANDSHAKE_PREFIX)):
                if(input == Input.HANDSHAKE_CERTIFICATE):
                    #handshake certificate packet
                    await mapper.hCertificate()
                elif(input == Input.HANDSHAKE_EMPTY_CERTIFICATE):
                    #handshake empty certificate packet
                    await mapper.hEmptyCertificate()
                elif(input == Input.HANDSHAKE_INVALID_CERTIFICATE):
                    #handshake empty certificate packet
                    await mapper.hInvalidCertificate()
                elif(input == Input.HANDSHAKE_CERTIFICATE_VERIFY):
                    #handshake certificate packet
                    await mapper.hCertificateVerify()
                elif(input == Input.HANDSHAKE_FINISHED or input == Input.HANDSHAKE_FINISHED_LOST_RESPONSE):
                    # handshake finished packet
                    await mapper.hFinished()
                elif(input == Input.HANDSHAKE_PING):
                    # handshake ping packet
                    if(mapper.target != Server.MVFST):
                        await mapper.hProbe()
                    else:
                        isSendPkt = False
                elif(input == Input.HANDSHAKE_CONNECTION_CLOSE):
                    # handshake connection close packet
                    await mapper.hConnectionClose()
                elif(input == Input.HANDSHAKE_EMPTY_PAYLOAD):
                    await mapper.hEmptyPayload()
                elif(input == Input.HANDSHAKE_UNEXPECTED_FRAME_TYPE):
                    await mapper.hUnexpectedFrameType()
                else:
                    prRed("ERROR: input not defined.")

            # Mapper config inputs
            elif(input.startswith(Input.MAPPER_CONFIG_PREFIX)):
                isSendPkt = False

                if(input == Input.INCLUDE_RETRY_TOKEN_OLD_OFFSET):
                    # update the token sent by the server in retry packet
                    await mapper.includeRetryToken(isNewConnection=False)
                elif(input == Input.INCLUDE_RETRY_TOKEN):
                    # reinitialise the mapper (update the token sent by the server in retry packet)
                    await mapper.includeRetryToken(isNewConnection=True)
                elif(input == Input.INCLUDE_INVALID_RETRY_TOKEN):
                    # reinitialise the mapper (using a invalid token, changing the last byte on the token received from the server)
                    await mapper.includeInvalidRetryToken(isNewConnection=True)
                elif(input == Input.CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL):
                    # change the packet's destination connection id field to what the mapper picked in its first Initial packet
                    if(mapper.target != Server.MVFST):
                        await mapper.changeDestinationConnectionID(isOriDestConID=True)                    
                elif(input == Input.CHANGE_DESTINATION_CONNECTION_ID_INITIAL):
                    # change the packet's destination connection id field to what the server picked in its first Initial packet
                    await mapper.changeDestinationConnectionID(isOriDestConID=False)                    
                elif(input == Input.REMOVE_PADDING_FROM_INITIAL_PACKETS):
                    # remove padding for subsequence Initial packets
                    await mapper.configureInitialPacketsPadding(isAddPadding=False)                    
                elif(input == Input.ADD_PADDING_TO_INITIAL_PACKETS):
                    # remove padding for subsequence Initial packets
                    await mapper.configureInitialPacketsPadding(isAddPadding=True)                    
                elif(input == Input.WAIT_SERVER_IDLE_TIMEOUT):
                    # wait unti server maximum idle timeout
                    await mapper.waitUntilServerMaxITO()
                elif(input == Input.DISCONNECT):
                    if(mapper.ableToDisconnect):
                        print("Disconnecting Mapper connection...\n")
                        return Input.DISCONNECT
                elif(input == Input.CREATE_DESTINATION_CONNECTION_ID):
                    await mapper.createAndUseInvalidDestConID()                    
                #elif(Input.CHANGE_DESTINATION_CONNECTION_ID in input):
                #    splitedList = input.split('-')
                #
                #    if(len(splitedList) > 1):
                #        conIDIndex = int(splitedList[1])
                #        await mapper.changeDestConID(conIDIndex)
                else:
                    prRed("ERROR: input not defined.")

            # Remaining inputs including: 1-RTT inputs
            else:
                if(input == Input.NORMAL_CONNECTION_CLOSE or input == Input.NORMAL_CONNECTION_CLOSE_WITHOUT_CHECKING):
                    # normal connection close packet
                    await mapper.nConnectionClose()           
                elif(input == Input.VALID_NEW_CONNECTION_ID):
                    # short header valid new connection ID
                    await mapper.sValidNewConnectionID()
                elif(input == Input.INVALID_NEW_CONNECTION_ID):
                    await mapper.sInvalidNewConnectionID()
                elif(input == Input.WAIT_LOST_RESPONSE):
                    pass                    
                elif(Input.ONE_RTT_PING in input):
                    await mapper.oneProbe()
                else:
                    prRed("ERROR: input not defined.")

            # to deal with MsQuic and Mvfst non-deterministic
            if(mapper.target != Server.MSQUIC and mapper.target != Server.MVFST):
                if((Input.INITIAL_CONNECTION_CLOSE in input or Input.HANDSHAKE_CONNECTION_CLOSE in input
                or Input.ZERORTT_CONNECTION_CLOSE in input or Input.NORMAL_CONNECTION_CLOSE in input 
                or input == Input.WAIT_SERVER_IDLE_TIMEOUT) and isSendPkt):
                    await asyncio.sleep(0.02)

                    if(MapperError.NOT_ABLE_TO_WRITE_CONNECTION_CLOSE not in mapper.connection.mapperError):
                        if(mapper.target == Server.QUICLY):
                            await asyncio.sleep(0.5)
                        elif(mapper.target == Server.KWIK or mapper.target == Server.PQUIC):
                            await asyncio.sleep(2)
                        elif(mapper.target == Server.QUANT):
                            await asyncio.sleep(1)
                        # 0.3 second for these servers because they have ~10s retry token exipry, this may solve non-determinisitic and the long learning time
                        elif(mapper.target == Server.NGTCP2 or mapper.target == Server.QUINN or mapper.target == Server.QUICGO):
                            await asyncio.sleep(0.3)
                        else:
                            await asyncio.sleep(1.2)

                        await mapper.checkServerClose()

            # print response lost msg
            if(Input.LOST_SYMBOL in input and not mapper.isLostResponseBefore):
                print("    Response Lost")
                mapper.isLostResponseBefore = True
            
            # do not wait and accept response when changing the internal config.
            if(isSendPkt):
                responseList = await mapper.getResponse(input=input, isLostWait = False)

            # set this so protocol will accept packets again
            await mapper.acceptResponse()
        elif(mapper.connection._state in END_STATES):
            responseList.append(Output.CONNECTION_CLOSED)
    
    responseList.append("end")

    return responseList

# fuzz to test if the retry token expired in 1 hour
# first send a initCltHello-vldACK
# Then, send initPing for 1 hour
# Lastly, [IncRetryTkn] and send initCltHello-vldACK
# Check if there is initSvrHello
async def testRetryTokenExp(args):
    print("Start to test the Retry token expiration (" + str(args.second) + "s)")

    # start server
    server = subprocess.Popen(args.run, shell=True, preexec_fn=os.setsid)
    await asyncio.sleep(1)

    # start mapper
    mapper = startConfigureMapper(args)
    await mapper.start()
    await mapper.initialize()

    # run 
    startTime = time()
    timer = args.second

    responseList = await fuzzIn(mapper, Input.INITIAL_CLIENT_HELLO_VALID_ACK)

    while(time() - startTime < timer):
        await fuzzIn(mapper, Input.INITIAL_PING)
        #await fuzzIn(mapper, Input.INITIAL_CLIENT_HELLO_VALID_ACK) # for quic-go
    
    await fuzzIn(mapper, Input.INCLUDE_RETRY_TOKEN)
    responseList += await fuzzIn(mapper, Input.INITIAL_CLIENT_HELLO_VALID_ACK)

    # write result
    resultDir = "testRetryExpResult"

    if(not os.path.exists(resultDir)):
        os.makedirs(resultDir)

    resultPath = resultDir + "/" + args.server + ".txt"

    with open(resultPath, "w") as resultFile:
        for response in responseList:
            resultFile.write(str(response) + "\n")

    # close mapper
    mapper.transport.close()
    await asyncio.sleep(1)

    # close server
    os.killpg(os.getpgid(server.pid), signal.SIGTERM)
    await asyncio.sleep(1)

# create 5000 connections and ping the server
# do not need to wait for response
async def pingServerToDeath(args):
    startingPort = args.port

    for i in range(10000):
        blockPrint()
        
        try:
            mapper = startConfigureMapper(args)
            await mapper.start()
            await mapper.initialize()
            # send Initial Ping
            # await mapper.iProbe()

            # send Initial Client Hello
            await mapper.iClientHelloValidInitialAck(cipherSuite=None)

            # enable the lines below to bypass the client address validation
            #await asyncio.sleep(0.05)
            #await mapper.includeRetryToken(isNewConnection=True)
            #await mapper.iProbe()

            mapper.transport.close()
        except Exception as e:
            print(e)

        if(int(args.port) < 65535):
            args.port = str(int(args.port) + 1)
        else:
            args.port = startingPort
        resumePrint()

# get the minimum time need to capture all the response from the server
# use Initial Client Hello because it will trigger one of the largest response in the handshake
# run 10 ten times and get the average
async def getShortTimeout(args):
    totalTime = 0
    
    for i in range(10):
        # start mapper
        mapper = startConfigureMapper(args)
        await mapper.start()
        await mapper.initialize()
        # send Initial Client Hello
        await mapper.iClientHelloValidInitialAck(cipherSuite=None)
        await asyncio.sleep(0.5)

        print("    -----Server's response: -----")

        for response in mapper.connection.peerResponse:
            print("    " + str(response))
        
        shortTimeout = mapper.connection.endTime - mapper.connection.startTime
        totalTime += shortTimeout
        print()

        # close mapper
        mapper.transport.close()
        await asyncio.sleep(0.5)
    
    avgShortTimeout = (totalTime/10) * 2
    print("The average short timeout for this server will be " + str(avgShortTimeout) + ".")

async def getSessionTicket(args):
    # remove the session ticket file
    if(os.path.exists(args.sessionTicket)):
        os.remove(args.sessionTicket)

    print("Getting Session Ticket Prior Fuzzing...")

    blockPrint()
    mapper = startConfigureMapper(args)
    await mapper.start()
    await mapper.initialize()

    await fuzzIn(mapper, Input.INITIAL_CLIENT_HELLO_VALID_ACK)
    await asyncio.sleep(0.1)

    # for quiche4j
    if(mapper.connection.receivedToken != b''):
        await fuzzIn(mapper, Input.INCLUDE_RETRY_TOKEN)
        await fuzzIn(mapper, Input.INITIAL_CLIENT_HELLO_VALID_ACK)

    await fuzzIn(mapper, Input.HANDSHAKE_FINISHED)
    await fuzzIn(mapper, Input.NORMAL_CONNECTION_CLOSE_WITHOUT_CHECKING)
    await asyncio.sleep(0.05)

    mapper.transport.close()
    await asyncio.sleep(0)

    resumePrint()
    print("Done.\n")

async def main(isSeq, args):
    
    if isSeq:
        seqList = []
        # Do not Remove these lines
        # seqList.append(['initCltHello-vldACK', 'hndFin'])
        # seqList.append(['initCltHello-vldACK', '[IncRetryTkn]', 'initCltHello-vldACK', 'hndFin'])
        # seqList.append(['initCltHello-vldACK', 'hndCert', 'hndCertVer', 'hndFin'])
        # seqList.append(['initCltHello-vldACK', '[IncRetryTkn]', 'initCltHello-vldACK', 'hndCert', 'hndCertVer', 'hndFin'])

        # ###################################################################################################################################################################################################################################################################################################################
        # Do not Remove the lines below
        # ###################################################################################################################################################################################################################################################################################################################
        # QT1 (Kwik; Retention of the unused encryption keys.)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED, Input.INITIAL_CONNECTION_CLOSE])

        # QT2 (Kwik; Implementation without a state machine.)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED])

        # QT3 (MsQuic; Does not issue its initial_source_connection_id at the correct connection state.)
        # seqList.append([Input.INITIAL_PING, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED])
        # seqList.append([Input.INITIAL_PING, Input.INCLUDE_RETRY_TOKEN, Input.INITIAL_PING, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED])
        # seqList.append([Input.INITIAL_PING, Input.INCLUDE_RETRY_TOKEN, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED])
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED, Input.INVALID_NEW_CONNECTION_ID])

        # QT4 (Neqo; NULL pointer dereference at neqo-transport/src/path.rs:147 when trying to get the primary path that is not initialized yet.)
        # seqList.append([Input.INITIAL_CONNECTION_CLOSE])

        # QT5 (Neqo; Limited connections due to a hardcoded value in the library: target/debug/build/neqo-crypto-a4be3db97961b0ce/out/nspr/pr/src/io/prlayer.c:619.)
        # for i in range(0, 32767):
        #    seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK])

        # QT6 (Picoquic BWCA; NULL pointer dereference due to incorrect way of prunning re-transmission queue in picoquic/sender.c:picoquic_implicit_handshake_ack(). Should be p->previous_packet instead of p->next_packet.)
        # seqList.append([Input.INITIAL_PING, Input.INITIAL_CLIENT_HELLO_INVALID_ACK])

        # QT7 (Picoquic BWR, BWRCA; Retry token tied to retry_source_connection_id.)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.INCLUDE_RETRY_TOKEN, Input.INITIAL_PING, Input.INITIAL_CLIENT_HELLO_VALID_ACK])

        # QT8 (PQUIC; Invalid original_destination_connection_id.)
        # seqList.append([Input.INITIAL_PING, Input.INITIAL_CLIENT_HELLO_VALID_ACK])

        # QT9 (PQUIC; Limitless active_connection_id_limit.)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED, Input.INVALID_NEW_CONNECTION_ID])

        # QT10 (PQUIC; Retention of the unused encryption keys.)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED, Input.INITIAL_CONNECTION_CLOSE])

        # QT11 (Quiche BWCA, BWRCA; Client authentication bypass using an empty certificate.)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_EMPTY_CERTIFICATE, Input.HANDSHAKE_FINISHED])

        # QT12 (Quiche4j; Concurrent modification exception in quiche4j/quiche4j-examples/src/main/java/io/quiche4j/examples/Http3Server.java:main():323.)
        # for i in range(0, 10):
        #    seqList.append([Input.INITIAL_PING, Input.INCLUDE_RETRY_TOKEN, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED])

        # QT13 (Quiche4j; Limitless active_connection_id_limit.)
        # seqList.append([Input.INITIAL_PING, Input.INCLUDE_RETRY_TOKEN, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED, Input.INVALID_NEW_CONNECTION_ID])

        # QT14 (Quant; Incorrect handling of an initialPing message.)
        # seqList.append([Input.INITIAL_PING])

        # QT15 (Quiwi; Does not close the connection when the number of received NEW_CONNECTION_ID frames exceed the active_connection_id_limit.)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED, Input.INVALID_NEW_CONNECTION_ID])

        # QT16 (XQUIC; Retention of the unused encryption keys.)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.INITIAL_CONNECTION_CLOSE])

        # QT17 (XQUIC; Maintaining a number of active connection IDs that exceed the active_connection_id_limit.)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED, Input.INVALID_NEW_CONNECTION_ID])

        # QT18 (PQUIC; NULL pointer dereference due to incorrect way of prunning re-transmission queue in picoquic/sender.c:picoquic_implicit_handshake_ack() (from Picoquic code).)
        # seqList.append([Input.INITIAL_PING, Input.INITIAL_CLIENT_HELLO_INVALID_ACK])

        # QT19 (Quant;Do not discard Initial packet with payload size less than 1200 bytes)
        # seqList.append([Input.REMOVE_PADDING_FROM_INITIAL_PACKETS, Input.INITIAL_CLIENT_HELLO_VALID_ACK])

        # QT20 (Quiche; Do not discard Initial packet with payload size less than 1200 bytes)
        # seqList.append([Input.REMOVE_PADDING_FROM_INITIAL_PACKETS, Input.INITIAL_CLIENT_HELLO_VALID_ACK])

        # QT21 (PQUIC; NULL pointer dereference due to not updating new_context_created when removing the new connection context in pquic/picoquic/packet.c:picoquic_incoming_initial():824.)
        # seqList.append([Input.INITIAL_CONNECTION_CLOSE])

        # QT22 - QT29 (Aioquic, LSQUIC, Neqo, Quic-go, Quinn, Quiwi, S2n-quic, XQUIC)
        # Note, Not a serious bug, only protocol violation: only discard the first Initial packet with no padding)
        # seqList.append([Input.INITIAL_PING, Input.REMOVE_PADDING_FROM_INITIAL_PACKETS, Input.INITIAL_CLIENT_HELLO_VALID_ACK])

        # QT30 (LSQuic; Accept Handshake packet from an unmatched Destination Connection ID even after the handshake is complete.)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL , Input.HANDSHAKE_FINISHED, Input.VALID_NEW_CONNECTION_ID])
        
        # QT31 - QT38 (Kwik, MsQuic, Quant, Quiche, Quic-go, Quiche4j, Quiwi, S2n-quic)
        # Specification violation: Accept Handshake packet from an unmatched Destination Connection ID until the handshake is complete.
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL , Input.HANDSHAKE_FINISHED, Input.INVALID_NEW_CONNECTION_ID])
        # Quiche4j
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.INCLUDE_RETRY_TOKEN, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL, Input.HANDSHAKE_FINISHED, Input.HANDSHAKE_PING])

        # QT39 (Quinn; unwrap() a None value when processing an unexpexted frame)
        # seqList.append([Input.INITIAL_PING, Input.INITIAL_UNEXPECTED_FRAME_TYPE])

        # QT40 (PQUIC; Buffer overflow when processing frame type 0x30)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_UNEXPECTED_FRAME_TYPE])

        # QT41 (PQUIC; Infinite loop when processing frame type 0xFF)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_UNEXPECTED_FRAME_TYPE])
        
        # QT42 (Aioquic; Accept Handshake packet from an unmatched Destination Connection ID.)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL , Input.HANDSHAKE_FINISHED])

        # QT43 (Aioquic; Does not close the connection when received an unexpected frame type)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_UNEXPECTED_FRAME_TYPE])

        # QT44 (Lsquic; Does not close the connection when received a packet without a frame and still acknowledge the packet.)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_EMPTY_PAYLOAD])

        # QT45-49 (MsQuic, Neqo, Quiche4j, Quinn, XQUIC; Does not close the connection when received a packet without a frame)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_EMPTY_PAYLOAD])
        # for Quiche4j (retry)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.INCLUDE_RETRY_TOKEN, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_EMPTY_PAYLOAD, Input.HANDSHAKE_FINISHED])

        # QT50 (Kwik; process Client Finished message sent in an 0-RTT packet; test with --getSessionTicket)
        # seqList.append(['initCltHello-invldACK_short', '0rttFin_short'])

        # QT51 (LSquic PSK config; Retain the Initial key until the handshake is confirmed)
        # seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.INITIAL_CONNECTION_CLOSE, Input.HANDSHAKE_FINISHED])

        # PQUIC
        # ['initCltHello-vldACK:AES-128-GCM-SHA256_short', '[ChgDestConID-Ori]', 'hndFin_long', 'hndConClose_short']

        ####################################################################################################################################################################################################################################################################################################################

        # close connection with an unmatched destination connection id
        # not vulnerable, the server is actually assume the Initial packet is another connection (this will not affect a client that discards the unused keys)
        #seqList.append(['initCltHello-vldACK', Input.HANDSHAKE_FINISHED, '[ChgDestConID-Ori]', 'initPing', '[ChgDestConID-Init]', 'VldNewConID'])

        # Not a bug (Quicly BWR; Send a new Retry token after the Retry token has been validated. In real, mapper just trigger 2 connection in one single connection)
        #seqList.append(['initPing', '[IncRetryTkn]', 'initPing', 'initConClose'])
        #seqList.append(['initPing', '[IncRetryTkn]', 'initPing', 'initConClose', '[IncRetryTkn]', 'initCltHello-vldACK'])
        #seqList.append(['initPing', '[IncInvldRetryTkn]', 'initCltHello-vldACK', 'initConClose', '[IncRetryTkn]', 'initCltHello-vldACK'])

        # to check if the server still accept the original destination connection id after handshake is done
        #seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED, Input.CHANGE_DESTINATION_CONNECTION_ID+'-0', Input.INVALID_NEW_CONNECTION_ID])

        # to check if the server still accept the original destination connection id during handshake
        #seqList.append([Input.INITIAL_PING, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.CREATE_DESTINATION_CONNECTION_ID,Input.HANDSHAKE_FINISHED, Input.CHANGE_DESTINATION_CONNECTION_ID+'-1', Input.HANDSHAKE_FINISHED])

        # to check if the server accepts a random id in the middle of handshake
        #seqList.append([Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.INCLUDE_RETRY_TOKEN, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED, Input.VALID_NEW_CONNECTION_ID, Input.INCLUDE_RETRY_TOKEN, Input.INITIAL_CLIENT_HELLO_VALID_ACK]) #, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.CREATE_DESTINATION_CONNECTION_ID, Input.HANDSHAKE_FINISHED, Input.INVALID_NEW_CONNECTION_ID])])

        # testing 0-RTT inputs
        # seqList.append(['initCltHello-vldACK','hndFin', '[Disconnect]', 'initCltHello-vldACK', '0rttPing', 'hndFin'])
        # seqList.append(['initCltHello-vldACK','hndFin', '[Disconnect]', 'initCltHello-vldACK', '0rttConClose', 'hndFin'])
        # seqList.append(['initCltHello-vldACK','hndFin', '[Disconnect]', 'initCltHello-vldACK', '0rttFin', 'hndFin'])
        # seqList.append(['initCltHello-vldACK','hndFin', '[Disconnect]', 'initCltHello-vldACK', '0rttNoFr', 'hndFin'])
        # seqList.append(['initCltHello-vldACK','hndFin', '[Disconnect]', 'initCltHello-vldACK', '0rttUnxpFrType', 'hndFin'])
        # seqList.append(['initCltHello-vldACK','hndFin', '[Disconnect]', 'initCltHello-vldACK', '0rttACK', 'hndFin'])

        #seqList.append(['initCltHello-invldACK_short'])
        # seqList.append(['initCltHello-vldACK','hndFin', 'InvldNewConID'])
        # seqList.append(['initCltHello-vldACK','[ChgDestConID-Ori]', 'hndFin'])
        # seqList.append(['initCltHello-vldACK','initConClose', 'hndFin'])

        # seqList.append(['initCltHello-vldACK_short', 'hndFin_short', '0rttConClose_short', 'hndUnxpFrType_short', 'hndUnxpFrType_short', '0rttNoFr_short'])
        # seqList.append(['initCltHello-vldACK_short', '0rttPing', 'hndFin_short'])
        # seqList.append(['initCltHello-vldACK_short', '[IncRetryTkn]', 'initCltHello-vldACK_short', 'hndFin_short'])
        # seqList.append(['initCltHello-vldACK_short', '[IncRetryTkn]','initCltHello-vldACK_short', 'hndFin', 'VldNewConID', '[ChgDestConID-Ori]', 'initConClose'])
        # seqList.append(['initPing_short', '[IncRetryTkn]', 'initCltHello-vldACK:AES-128-GCM-SHA256_short', 'hndFin_short'])
        seqList.append(['initCltHello-vldACK', 'hndEmpCert', 'hndCertVer', 'hndFin'])
        # seqList.append(['initCltHello-vldACK_long', 'hndCert_long', 'hndCertVer_long', 'hndFin_long'])
        # seqList.append(['[RmPadFrmInitPkts]', 'initPing_short'])
        # seqList.append(['initCltHello-vldACK_short', 'initCltHello-vldACK','[ChgDestConID-Ori]', '0rttACK', 'hndFin'])
        # seqList.append(['initCltHello-vldACK_short', 'hndFin_short', 'VldNewConID', '0rttConClose'])
        # seqList.append(['initCltHello-invldACK_short', 'initPing_short'])#, 'hndFin', 'initPing'])
        # seqList.append(['initCltHello-invldACK_short', '[IncRetryTkn]', 'hndFin', 'initPing'])
        # seqList.append(['initCltHello-vldACK_short', '[ChgDestConID-Ori]', 'hndFin_short', '[RmPadFrmInitPkts]', 'hndNoFr_short', '0rttConClose_short'])
        

        # Non-deterministic in Neqo
        #seqList.append(['initCltHello-vldACK_short', '0rttACK_short'])

        # Non-deterministic in Pquic
        # seqList.append(['initCltHello-vldACK_short', '[ChgDestConID-Ori]', 'hndFin_short', '[RmPadFrmInitPkts]', 'hndNoFr_short', '0rttConClose_short'])
        
        # fuzz few sequences to server
        for sequence in seqList:
            if(args.getSessionTicket and not os.path.exists(args.sessionTicket)):
                await getSessionTicket(args)
            
            await fuzzSeq(sequence)
        
        # Once all the sequences are done, remove the session ticket here
        if(os.path.exists(args.sessionTicket)):
            os.remove(args.sessionTicket)

    elif(args.testRetryTokenExp):
        await testRetryTokenExp(args)
    elif(args.getShortTimeout):
        await getShortTimeout(args)
    elif(args.pingServerToDeath):
        await pingServerToDeath(args)
    else:
        # if the input dictionary is PSK, get the session ticket before fuzzing
        if(args.getSessionTicket and not os.path.exists(args.sessionTicket)):
            await getSessionTicket(args)
        
        mapper = startConfigureMapper(args)
        await mapper.start()
        await mapper.initialize()
        
        inputPath = "run/input_" + args.port + ".txt"
        outputPath = "run/output_" + args.port + ".txt"
        inCount = 0   
        input = ""
        
        while input != "end":
            try:    
                with open(inputPath, "r") as inFile:
                    lines = inFile.readlines()

                    if(len(lines) > inCount):
                        input = lines[inCount].split("\n")[0]
                        inCount += 1
                    else:
                        input = ""
            except:
                continue

            if(input != "end" and input != ""):
                responseList = await fuzzIn(mapper, input)
                
                # disconnect the previous connection and close the connection socket
                # reconfigure the Mapper to use the session ticket on a new connection
                if(responseList == Input.DISCONNECT):
                    with open(outputPath, "a") as outFile:
                        outFile.write("\nend\n")

                    mapper.transport.close()
                    await asyncio.sleep(0)
                    mapper = startConfigureMapper(args)
                    await mapper.start()
                    await mapper.initialize()
                else:
                    with open(outputPath, "a") as outFile:
                        for response in responseList:
                            outFile.write(str(response) + "\n")

        # close the transport layer
        mapper.transport.close()
  
        if(args.getSessionTicket):
            # remove the session ticket file under 2 conditions:
            # 1) Mapper has not use the session ticket
            # 2) Mapper has establish a new connection and get a new session ticket
            # always remove pquic session ticket when using findND
            if(mapper.ableSend0RTTState == Send0rttState.READY or mapper.target == Server.PQUIC or mapper.target == Server.KWIK):
                if(os.path.exists(args.sessionTicket)):
                    os.remove(args.sessionTicket)
        elif(os.path.exists(args.sessionTicket)):
            # remove the session ticket if --getSessionTicket is not set
            os.remove(args.sessionTicket)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence", action="store_true", help="Fuzz a list of sequence only.")
    parser.add_argument("-s", "--server", choices=Server.LIST, 
                        help="Target QUIC server.", required="--getShortTimeout" not in sys.argv)
    parser.add_argument("--cipher", choices=["None", "AES-128-GCM-SHA256", "AES-256-GCM-SHA384", "CHACHA20-POLY1305-SHA256"], default="None", 
                        help="Cipher suites that are currently supported.")
    parser.add_argument("-p", "--port", type=str,
                        default="3344",
                        help="Mapper port.")
    parser.add_argument("-t", "--targetPort", type=str,
                        default="4433",
                        help="Target port.")
    parser.add_argument("-c", "--certificate", type=str,
                        default="../secrets/clientCert/client-cert.pem",
                        help="Load the TLS certificate from the specified file.")
    parser.add_argument("-k", "--privateKey", type=str,
                        default="../secrets/clientCert/client-key.pem",
                        help="Load the TLS private key from the specified file.")
    parser.add_argument("--invalidCertificate", type=str, 
                        default="../secrets/invalidCert/invalid-cert.pem",
                        help="Load the invalid certificate from the specified file.")
    parser.add_argument("--caCert", type=str, 
                        default="../secrets/caCert/ca-cert.pem",
                        help="CA cert for verify peer certificate.")
    parser.add_argument("--secrets", type=str, 
                        default="../secrets/mapperSecrets.log",
                        help="File to store the secrets (use in Wireshark late).")
    parser.add_argument("--log", type=str,
                        help="Log file, enable log and store log in this file.")
    parser.add_argument("-i", "--input", choices=["B", "BWR", "BWCA", "BWRCA", "B-s", "BWR-s", "BWCA-s", "BWRCA-s", "B-l", "BWR-l", "BWCA-l", "BWRCA-l", "PSK-s", "PSKWR-s"], 
                          default="B", help="Input dictionary: B(basic), BWR(B + retry), BWCA(B + client authentication), BWRCA(BWCA + retry).")
    parser.add_argument("--count", type=str, default=None,
                        help="Iteration count from the Learner.")
    parser.add_argument("--sessionTicket", type=str, default="sessionTicket",
                        help="File to read/write the session ticket used for 0-RTT.")
    parser.add_argument("--getShortTimeout", action="store_true", help="Get the minimum time required to capture all the server's responses.")
    parser.add_argument("--testRetryTokenExp", action="store_true", help="Test retry token expiration.")
    parser.add_argument("--second", type=int,  required="--testRetryTokenExp" in sys.argv,
                        help="Time in second to test the Retry Token expiration.")
    parser.add_argument("-r", "--run", required="--testRetryTokenExp" in sys.argv,
                        help="Command to run the target server (FOR TEST RETRY TOKEN EXPIRATION ONLY).")
    parser.add_argument("--pingServerToDeath", action="store_true", default=False,
                        help="Create 10000 connection and ping the server.")
    parser.add_argument("--getSessionTicket", action="store_true", default=False,
                        help="Create a Basic connection and get a session ticket prior the fuzzing start.")
    

    args = parser.parse_args()

    if(args.sequence):
        asyncio.run(main(isSeq=True, args=args))
    else:
        if(args.count):
            print("msg chain count = " + str(args.count))

        asyncio.run(main(isSeq=False, args=args))
