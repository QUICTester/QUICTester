# QT6

## Bug Description
Upon attempts to retransmit a previously sent packet, a null pointer is dereferenced while parsing the list. This is caused by an incorrect method of pruning the re-transmission queue in ```picoquic/sender.c:picoquic_implicit_handshake_ack()```. Should be ```p->previous_packet``` instead of ```p->next_packet```.

## Impacted Servers & Versions
Picoquic (Tested on commit d2f01093)

## Input Sequence
[Input.INITIAL_PING, Input.INITIAL_CLIENT_HELLO_INVALID_ACK]
