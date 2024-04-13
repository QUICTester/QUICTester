# QT7

## Bug Description
Retry token tied to retry_source_connection_id

## Impacted Servers & Versions
Picoquic (Tested on commit d2f01093)

## Input Sequence
[Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.INCLUDE_RETRY_TOKEN, Input.INITIAL_PING, Input.INITIAL_CLIENT_HELLO_VALID_ACK]
