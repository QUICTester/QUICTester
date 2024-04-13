# QT1

## Bug Description
Once a key is created for an encryption level, the Kwik server will continue decrypting and processing packets from that encryption level, even after moving to a new encryption level.

## Impacted Servers & Versions
Kwik (Tested on commit 745fd4e2)

## Input Sequence
[Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED, Input.INITIAL_CONNECTION_CLOSE]
