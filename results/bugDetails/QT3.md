# QT3

## Bug Description
MsQuic server deviates from the specification by selecting its Source Connection ID only when receiving the INITIAL_CLIENT_HELLO message, rather than the first Initial packet.

## Impacted Servers & Versions
MsQuic (Tested on commit 5c070cdc)

## Input Sequence
[Input.INITIAL_PING, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED]
