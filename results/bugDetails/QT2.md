# QT2 ([CVE-2024-22590](https://nvd.nist.gov/vuln/detail/CVE-2024-22590))

## Bug Description
The Kwik implementation would reprocess a message that has already been successfully processed before, such as an INITIAL_CLIENT_HELLO message. Note that this message contains application protocol negotiation, transport parameters, and cryptographic information to perform key exchange. This reprocessing of an INITIAL_CLIENT_HELLO message will overwrite the existing connection's application protocol version, transport parameters, and encryption key. 

Combined with the [QT1](QT1.md), attackers can reset or potentially hijack a victim’s connection using a initialClientHello message. For example, at any state of a connection, an attacker with the victim’s Initial
key can send a spoofed initialClientHello message with transport parameters and cryptographic information that differs from the victim’s to the Kwik server. The Kwik server will process the spoofed initialClientHello message and overwrite the existing transport parameters and encryption key that it has with the victim. Due to the desynchronization of transport parameters and encryption keys, the server no longer recognizes the victim and drops any packets coming from the victim. An attacker can then sniff the responses from the server, complete the overwritten handshake and use the connection to exchange data with the server.

## Impacted Servers & Versions
Kwik (Tested on commit 745fd4e2)

## Fixed Version
This bug was fixed in commit [11862d5](https://github.com/ptrd/kwik/commit/11862d54d72de63abd0b76ca6bb9df56e634212c).

## Input Sequence
[Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.INITIAL_CLIENT_HELLO_VALID_ACK, Input.HANDSHAKE_FINISHED]
