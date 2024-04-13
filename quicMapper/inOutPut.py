# 
# Input and output for learner and mapper

from http.client import PROXY_AUTHENTICATION_REQUIRED

class Input:
    LOST_SYMBOL = "-l"
    SHORT_SYMBOL = "_short"
    LONG_SYMBOL = "_long"
    INITIAL_PREFIX = "init"
    ZERORTT_PREFIX = "0rtt"
    HANDSHAKE_PREFIX = "hnd"
    MAPPER_CONFIG_PREFIX = "["
    
    VALID_ACK_SYMBOL = "-vldACK"
    INVALID_ACK_SYMBOL = "-invldACK"
    CIPHER_SYMBOL = ":"

    ####################### Original Inputs #################################
    # normal
    NORMAL_CONNECTION_CLOSE = "norConClose"
    NORMAL_CONNECTION_CLOSE_WITHOUT_CHECKING = "normalConnectionCloseNoCheck"
    CREATE_DESTINATION_CONNECTION_ID = "createDestConID"
    CHANGE_DESTINATION_CONNECTION_ID = "chgDestConIDByIndex" # add "-#" at the end when use, # will be the index of the destConIDList

    # initial
    INITIAL_PING = "initPing"
    INITIAL_CLIENT_HELLO = "initCltHello"
    INITIAL_CLIENT_HELLO_VALID_ACK = "initCltHello-vldACK"
    INITIAL_CLIENT_HELLO_INVALID_ACK = "initCltHello-invldACK"
    INITIAL_CONNECTION_CLOSE = "initConClose"
    INITIAL_CLIENT_HELLO_LOST_RESPONSE = "initCltHello-lostRes"
    INITIAL_EMPTY_PAYLOAD = "initNoFr"
    INITIAL_UNEXPECTED_FRAME_TYPE = "initUnxpFrType"

    # for different cipher suites
    INITIAL_CLIENT_HELLO_VALID_ACK_AES_128_GCM_SHA256 = "initCltHello-vldACK:AES-128-GCM-SHA256"
    INITIAL_CLIENT_HELLO_VALID_ACK_AES_256_GCM_SHA384 = "initCltHello-vldACK:AES-256-GCM-SHA384"
    INITIAL_CLIENT_HELLO_VALID_ACK_CHACHA20_POLY1305_SHA256 = "initCltHello-vldACK:CHACHA20-POLY1305-SHA256"
    INITIAL_CLIENT_HELLO_INVALID_ACK_AES_128_GCM_SHA256 = "initCltHello-invldACK:AES-128-GCM-SHA256"
    INITIAL_CLIENT_HELLO_INVALID_ACK_AES_256_GCM_SHA384 = "initCltHello-invldACK:AES-256-GCM-SHA384"
    INITIAL_CLIENT_HELLO_INVALID_ACK_CHACHA20_POLY1305_SHA256 = "initCltHello-invldACK:CHACHA20-POLY1305-SHA256"

    # 0-RTT
    ZERORTT_PING = "0rttPing"
    ZERORTT_CONNECTION_CLOSE = "0rttConClose"
    ZERORTT_FINISHED = "0rttFin"
    ZERORTT_EMPTY_PAYLOAD = "0rttNoFr"
    ZERORTT_UNEXPECTED_FRAME_TYPE = "0rttUnxpFrType"
    ZERORTT_ACK = "0rttACK" # not stable yet
    # ack ?

    # handshake
    HANDSHAKE_PING = "hndPing"
    HANDSHAKE_CERTIFICATE = "hndCert"
    HANDSHAKE_EMPTY_CERTIFICATE = "hndEmpCert"
    HANDSHAKE_INVALID_CERTIFICATE = "hndInvldCert"
    HANDSHAKE_CERTIFICATE_VERIFY = "hndCertVer"
    HANDSHAKE_FINISHED = "hndFin"
    HANDSHAKE_FINISHED_LOST_RESPONSE = "hndFin-lostRes"
    HANDSHAKE_CONNECTION_CLOSE = "hndConClose"
    HANDSHAKE_EMPTY_PAYLOAD = "hndNoFr"
    HANDSHAKE_UNEXPECTED_FRAME_TYPE = "hndUnxpFrType"

    # post handshake
    VALID_NEW_CONNECTION_ID = "VldNewConID"
    INVALID_NEW_CONNECTION_ID = "InvldNewConID"
    ONE_RTT_PING = "1rttPing"

    # mapper's behaviour
    INCLUDE_INVALID_RETRY_TOKEN = "[IncInvldRetryTkn]"
    INCLUDE_RETRY_TOKEN_OLD_OFFSET = "[IncRetryTkn-OldOffset]"
    INCLUDE_RETRY_TOKEN = "[IncRetryTkn]"
    CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL = "[ChgDestConID-Ori]"
    CHANGE_DESTINATION_CONNECTION_ID_INITIAL = "[ChgDestConID-Init]"
    REMOVE_PADDING_FROM_INITIAL_PACKETS = "[RmPadFrmInitPkts]"
    ADD_PADDING_TO_INITIAL_PACKETS = "[AddPadToInitPkts]"
    DISCONNECT = "[Disconnect]"
    SECOND_CONNECTION = "[SecondConn]"
    WAIT_SERVER_IDLE_TIMEOUT = "[IDLE]"
    WAIT_LOST_RESPONSE= "[WAIT]"

    # inputs that are currently in the base dictionary that use to configure the Mapper
    mapperConfigInput = [INCLUDE_RETRY_TOKEN, CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL, REMOVE_PADDING_FROM_INITIAL_PACKETS, DISCONNECT]


class Output:
    # normal
    PING_ACKED = "PingACK"
    NORMAL_ACK = "norACK"
    NORMAL_CONNECTION_CLOSE = "ConClose"

    # initial
    INITIAL_SERVER_HELLO = "initSvrHello"

    # retry
    RETRY = "retry"

    # version negotiation
    VERSION_NEGOTIATION = "verNego"

    # handshake
    HANDSHAKE_ENCRYPTED_EXTENSIONS = "hndEncExt"
    HANDSHAKE_CERTIFICATE_REQUEST = "hndCertReq"
    HANDSHAKE_CERTIFICATE = "hndCert"
    HANDSHAKE_CERTIFICATE_VERIFY = "hndCertVer"
    HANDSHAKE_FINISHED = "hndFin"

    # post handshake
    HANDSHAKE_DONE = "HndshkDone"
    NEW_TOKEN = "NewToken"
    NEW_SESSION_TICKET = "NewSessionTicket"
    VALID_NEW_CONNECTION_ID = "VldNewConID"

    # mapper's behaviour
    WRITE_CONNECTION_CLOSE_ERROR = "[WrtConCloseErr]"
    WRITE_NEW_CONNECTION_ID_ERROR = "[WrtNewConIDErr]"
    MAPPER_WRITE_FAILED = "[WrtFail]"

    # server's behaviour
    CONNECTION_CLOSED = "<ConClosed>"
    CONNETION_ACTIVE = "<ConAct>"

# server name, server short timeout, server long timeout
class Server:
    AIOQUIC = "aioquic"
    AIOQUIC_SHORT = 0.1
    AIOQUIC_LONG = 0.55

    GOOGLEQUIC = "google-quiche"
    GOOGLEQUIC_SHORT = 0.05
    GOOGLEQUIC_LONG = 0.5

    KWIK = "kwik"
    KWIK_SHORT = 0.25
    KWIK_LONG = 0.7

    LSQUIC = "lsquic"
    LSQUIC_SHORT = 0.05
    LSQUIC_LONG = 0.5

    MSQUIC = "msquic"
    MSQUIC_SHORT = 0.05 # initial 0.1 # current 0.025 # 0.05(usenix)
    MSQUIC_LONG = 0.5 #0.55

    MVFST = "mvfst"
    MVFST_SHORT = 0.05 # initial 0.1 # current 0.025
    MVFST_LONG = 0.5 #0.55

    NEQO = "neqo"
    NEQO_SHORT = 0.05 # 0.065
    NEQO_LONG = 0.5 #0.55
    NEQO_SHORT_RETRY = 0.065 # for retry (due to retry token expiry 5s)
    NEQO_LONG_RETRY = 0.15 # for retry (due to retry token expiry 5s)

    NGTCP2 = "ngtcp2"
    NGTCP2_SHORT = 0.05
    NGTCP2_LONG = 0.5 #0.4 for BWRCA-l # 0.5 #0.35 for results

    PICOQUIC = "picoquic"
    PICOQUIC_SHORT = 0.15 # ~0.0006
    PICOQUIC_LONG = 0.6

    PQUIC = "pquic"
    PQUIC_SHORT = 0.2 #0.15 for other config # 0.2 for PSK config
    PQUIC_LONG = 0.6

    QUANT = "quant"
    QUANT_SHORT = 0.05
    QUANT_LONG = 0.5

    QUICHE = "quiche"
    QUICHE_SHORT = 0.2 #0.05
    QUICHE_LONG = 0.5  #0.5 #0.4 for results

    QUICHE4J = "quiche4j"
    QUICHE4J_SHORT = 0.2
    QUICHE4J_LONG = 0.5 

    QUICGO = "quic-go"
    QUICGO_SHORT = 0.05 
    QUICGO_LONG = 0.5 #0.35 for results # 0.5

    QUICLY = "quicly"
    QUICLY_SHORT = 0.05 #use 0.05 now because handshake timeout has been temporary removed # use small value because of its handshake timeout 0.02
    QUICLY_LONG = 0.5 # use 0.5 use now because handshake timeout has been temporary removed # small value because of its handshake timeout 0.08

    QUINN = "quinn"
    QUINN_SHORT = 0.05 # 0.08
    QUINN_LONG = 0.5 # 0.53

    QUIWI = "quiwi"
    QUIWI_SHORT = 0.05
    QUIWI_LONG = 0.2 #0.3

    S2NQUIC = "s2n-quic"
    S2NQUIC_SHORT = 0.05 
    S2NQUIC_LONG = 0.5 #0.4 
    S2NQUIC_SHORT_RETRY = 0.05 # for retry (due to retry token expiry 1s)
    S2NQUIC_LONG_RETRY = 0.08  # for retry (due to retry token expiry 1s)    

    XQUIC = "xquic"
    XQUIC_SHORT = 0.05
    XQUIC_LONG = 0.5

    LIST = [AIOQUIC, GOOGLEQUIC, KWIK, LSQUIC, MSQUIC, MVFST, NEQO, NGTCP2, PICOQUIC, PQUIC, QUANT, QUICHE, QUICHE4J, QUICGO, QUICLY, QUINN, QUIWI, S2NQUIC, XQUIC]

class InputDictionary:
    # inputs for testing the learning library
    TEST = [Input.INITIAL_PING, Input.INITIAL_CONNECTION_CLOSE]

    # inputs for Basic (B)
    BASIC = [Input.INITIAL_PING, Input.INITIAL_CONNECTION_CLOSE,
             Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_128_GCM_SHA256, Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_256_GCM_SHA384, 
             Input.INITIAL_CLIENT_HELLO_VALID_ACK_CHACHA20_POLY1305_SHA256,
             Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_128_GCM_SHA256, Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_256_GCM_SHA384, 
             Input.INITIAL_CLIENT_HELLO_INVALID_ACK_CHACHA20_POLY1305_SHA256, Input.INITIAL_EMPTY_PAYLOAD, Input.INITIAL_UNEXPECTED_FRAME_TYPE,
             Input.HANDSHAKE_PING, Input.HANDSHAKE_FINISHED, Input.HANDSHAKE_CONNECTION_CLOSE,
             Input.HANDSHAKE_EMPTY_PAYLOAD, Input.HANDSHAKE_UNEXPECTED_FRAME_TYPE,
             Input.VALID_NEW_CONNECTION_ID, Input.INVALID_NEW_CONNECTION_ID,
             Input.CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL, Input.REMOVE_PADDING_FROM_INITIAL_PACKETS]
    
    # inputs for Basic with Retry (BWR)
    BASIC_WITH_RETRY = [Input.INITIAL_PING, Input.INITIAL_CONNECTION_CLOSE,
                        Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_128_GCM_SHA256, Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_256_GCM_SHA384, 
                        Input.INITIAL_CLIENT_HELLO_VALID_ACK_CHACHA20_POLY1305_SHA256,
                        Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_128_GCM_SHA256, Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_256_GCM_SHA384, 
                        Input.INITIAL_CLIENT_HELLO_INVALID_ACK_CHACHA20_POLY1305_SHA256, Input.INITIAL_EMPTY_PAYLOAD, Input.INITIAL_UNEXPECTED_FRAME_TYPE,
                        Input.HANDSHAKE_PING, Input.HANDSHAKE_FINISHED, Input.HANDSHAKE_CONNECTION_CLOSE, 
                        Input.HANDSHAKE_EMPTY_PAYLOAD, Input.HANDSHAKE_UNEXPECTED_FRAME_TYPE,
                        Input.VALID_NEW_CONNECTION_ID, Input.INVALID_NEW_CONNECTION_ID,
                        Input.CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL, Input.REMOVE_PADDING_FROM_INITIAL_PACKETS,
                        Input.INCLUDE_RETRY_TOKEN]
    
    # inputs for Basic with Client Authentication (BWCA)
    BASIC_WITH_CA = [Input.INITIAL_PING, Input.INITIAL_CONNECTION_CLOSE,
                     Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_128_GCM_SHA256, Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_256_GCM_SHA384, 
                     Input.INITIAL_CLIENT_HELLO_VALID_ACK_CHACHA20_POLY1305_SHA256,
                     Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_128_GCM_SHA256, Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_256_GCM_SHA384, 
                     Input.INITIAL_CLIENT_HELLO_INVALID_ACK_CHACHA20_POLY1305_SHA256, Input.INITIAL_EMPTY_PAYLOAD, Input.INITIAL_UNEXPECTED_FRAME_TYPE,
                     Input.HANDSHAKE_PING, Input.HANDSHAKE_FINISHED, Input.HANDSHAKE_CONNECTION_CLOSE, 
                     Input.HANDSHAKE_EMPTY_PAYLOAD, Input.HANDSHAKE_UNEXPECTED_FRAME_TYPE,
                     Input.VALID_NEW_CONNECTION_ID, Input.INVALID_NEW_CONNECTION_ID,
                     Input.CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL, Input.REMOVE_PADDING_FROM_INITIAL_PACKETS,
                     Input.HANDSHAKE_CERTIFICATE, Input.HANDSHAKE_CERTIFICATE_VERIFY, 
                     Input.HANDSHAKE_EMPTY_CERTIFICATE, Input.HANDSHAKE_INVALID_CERTIFICATE]
    
    # inputs for Basic with Retry and Client Authentication (BWRCA)
    BASIC_WITH_RETRY_CA = [Input.INITIAL_PING, Input.INITIAL_CONNECTION_CLOSE,
                           Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_128_GCM_SHA256, Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_256_GCM_SHA384, 
                           Input.INITIAL_CLIENT_HELLO_VALID_ACK_CHACHA20_POLY1305_SHA256,
                           Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_128_GCM_SHA256, Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_256_GCM_SHA384, 
                           Input.INITIAL_CLIENT_HELLO_INVALID_ACK_CHACHA20_POLY1305_SHA256, Input.INITIAL_EMPTY_PAYLOAD, Input.INITIAL_UNEXPECTED_FRAME_TYPE,
                           Input.HANDSHAKE_PING, Input.HANDSHAKE_FINISHED, Input.HANDSHAKE_CONNECTION_CLOSE, 
                           Input.HANDSHAKE_EMPTY_PAYLOAD, Input.HANDSHAKE_UNEXPECTED_FRAME_TYPE,
                           Input.VALID_NEW_CONNECTION_ID, Input.INVALID_NEW_CONNECTION_ID,
                           Input.CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL, Input.REMOVE_PADDING_FROM_INITIAL_PACKETS,
                           Input.INCLUDE_RETRY_TOKEN,
                           Input.HANDSHAKE_CERTIFICATE, Input.HANDSHAKE_CERTIFICATE_VERIFY, 
                           Input.HANDSHAKE_EMPTY_CERTIFICATE, Input.HANDSHAKE_INVALID_CERTIFICATE]
    
    #PSK = [Input.INITIAL_PING, Input.INITIAL_CONNECTION_CLOSE,
    #         Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_128_GCM_SHA256, Input.INITIAL_CLIENT_HELLO_VALID_ACK_AES_256_GCM_SHA384, 
    #         Input.INITIAL_CLIENT_HELLO_VALID_ACK_CHACHA20_POLY1305_SHA256,
    #         Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_128_GCM_SHA256, Input.INITIAL_CLIENT_HELLO_INVALID_ACK_AES_256_GCM_SHA384, 
    #         Input.INITIAL_CLIENT_HELLO_INVALID_ACK_CHACHA20_POLY1305_SHA256, Input.INITIAL_EMPTY_PAYLOAD, Input.INITIAL_UNEXPECTED_FRAME_TYPE,
    #         Input.HANDSHAKE_PING, Input.HANDSHAKE_FINISHED, Input.HANDSHAKE_CONNECTION_CLOSE,
    #         Input.HANDSHAKE_EMPTY_PAYLOAD, Input.HANDSHAKE_UNEXPECTED_FRAME_TYPE,
    #         Input.VALID_NEW_CONNECTION_ID, Input.INVALID_NEW_CONNECTION_ID, Input.ZERORTT_PING,
    #         Input.CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL, Input.REMOVE_PADDING_FROM_INITIAL_PACKETS]

    # inputs for Pre-Shared Key
    PSK = [Input.INITIAL_PING, Input.INITIAL_CONNECTION_CLOSE,
             Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.INITIAL_CLIENT_HELLO_INVALID_ACK, 
             Input.INITIAL_EMPTY_PAYLOAD, Input.INITIAL_UNEXPECTED_FRAME_TYPE,
             Input.HANDSHAKE_PING, Input.HANDSHAKE_FINISHED, Input.HANDSHAKE_CONNECTION_CLOSE,
             Input.HANDSHAKE_EMPTY_PAYLOAD, Input.HANDSHAKE_UNEXPECTED_FRAME_TYPE,
             Input.VALID_NEW_CONNECTION_ID, Input.INVALID_NEW_CONNECTION_ID, 
             Input.ZERORTT_PING, Input.ZERORTT_CONNECTION_CLOSE, Input.ZERORTT_FINISHED,
             Input.ZERORTT_EMPTY_PAYLOAD, Input.ZERORTT_UNEXPECTED_FRAME_TYPE, Input.ZERORTT_ACK,
             Input.CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL, Input.REMOVE_PADDING_FROM_INITIAL_PACKETS]
    
    # inputs for Pre-Shared Key with Retry
    PSK_WITH_RETRY = [Input.INITIAL_PING, Input.INITIAL_CONNECTION_CLOSE,
             Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.INITIAL_CLIENT_HELLO_INVALID_ACK, 
             Input.INITIAL_EMPTY_PAYLOAD, Input.INITIAL_UNEXPECTED_FRAME_TYPE,
             Input.HANDSHAKE_PING, Input.HANDSHAKE_FINISHED, Input.HANDSHAKE_CONNECTION_CLOSE,
             Input.HANDSHAKE_EMPTY_PAYLOAD, Input.HANDSHAKE_UNEXPECTED_FRAME_TYPE,
             Input.VALID_NEW_CONNECTION_ID, Input.INVALID_NEW_CONNECTION_ID, 
             Input.ZERORTT_PING, Input.ZERORTT_CONNECTION_CLOSE, Input.ZERORTT_FINISHED,
             Input.ZERORTT_EMPTY_PAYLOAD, Input.ZERORTT_UNEXPECTED_FRAME_TYPE, Input.ZERORTT_ACK,
             Input.CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL, Input.REMOVE_PADDING_FROM_INITIAL_PACKETS,
             Input.INCLUDE_RETRY_TOKEN]
    
    # # inputs for Pre-Shared Key with Retry
    # PSK_WITH_RETRY = [Input.INITIAL_PING, Input.INITIAL_CONNECTION_CLOSE,
    #          Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.INITIAL_CLIENT_HELLO_INVALID_ACK, 
    #          Input.INITIAL_EMPTY_PAYLOAD, Input.INITIAL_UNEXPECTED_FRAME_TYPE,
    #          Input.HANDSHAKE_PING, Input.HANDSHAKE_FINISHED, Input.HANDSHAKE_CONNECTION_CLOSE,
    #          Input.HANDSHAKE_EMPTY_PAYLOAD, Input.HANDSHAKE_UNEXPECTED_FRAME_TYPE,
    #          Input.VALID_NEW_CONNECTION_ID, Input.INVALID_NEW_CONNECTION_ID, 
    #          Input.ZERORTT_CONNECTION_CLOSE, Input.ZERORTT_FINISHED,
    #          Input.ZERORTT_EMPTY_PAYLOAD, Input.ZERORTT_UNEXPECTED_FRAME_TYPE, Input.ZERORTT_ACK,
    #          Input.CHANGE_DESTINATION_CONNECTION_ID_ORIGINAL, Input.REMOVE_PADDING_FROM_INITIAL_PACKETS]
    
    # generate the input dictionary based on the base dictionary and given timeout settings
    def generateInputDictionary(baseDictionary, timeout):
        inputDictionary = []

        for input in baseDictionary:
            # generate short inputs
            if(input not in Input.mapperConfigInput):
                if(timeout == Input.SHORT_SYMBOL):
                    inputDictionary.append((input + Input.SHORT_SYMBOL))
                # generate long inputs
                elif(timeout == Input.LONG_SYMBOL):
                    inputDictionary.append((input + Input.LONG_SYMBOL))
                # generate mixed inputs
                else:
                    inputDictionary.append((input + Input.SHORT_SYMBOL))
                    inputDictionary.append((input + Input.LONG_SYMBOL))
            else:
                inputDictionary.append((input))
        
        return inputDictionary

            