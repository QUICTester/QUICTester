# QT1

## Bug Description
Once a key is created for an encryption level, the Kwik server will continue decrypting and processing packets from that encryption level, even after moving to a new encryption level. This allows attackers to disrupt a connection with a PSK configuration by sending a CONNECTION_CLOSE frame that is encrypted via the initial key computed. Network traffic sniffing is needed as part of exploitation.

## Impacted Servers & Versions
Kwik (Tested on commit 745fd4e2)

## Fixed Version
This bug was fixed in commit [040b0d1](https://github.com/ptrd/kwik/commit/040b0d1327bfb0a8e35c23c2bd612a4a39b721d4).

## Input Sequence
[Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED, Input.INITIAL_CONNECTION_CLOSE]
