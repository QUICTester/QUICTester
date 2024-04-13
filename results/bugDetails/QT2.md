# QT2

## Bug Description
The Kwik implementation would reprocess a message that has already been successfully processed before, such as an INITIAL_CLIENT_HELLO message. Note that this message contains application protocol negotiation, transport parameters, and cryptographic information to perform key exchange. This reprocessing of an INITIAL_CLIENT_HELLO message will overwrite the existing connection's application protocol version, transport parameters, and encryption key.

## Impacted Servers & Versions
Kwik (Tested on commit 745fd4e2)

## Input Sequence
[Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED]
