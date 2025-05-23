# 🐛 Bugs Found

| Bug ID | Server | Description | Details |
| :----- | :----- | :---------- | :------------- |
| S-1    | Aioquic (239f99b8) | Specification violation: Does not close the connection when receiving an unexpected frame type | [Click for more info](bugDetails/S-1.md) |
| S-2    | Kwik (745fd4e2) | Specification violation ([CVE-2024-22588](https://nvd.nist.gov/vuln/detail/CVE-2024-22588)): Retention of the unused encryption keys. | [Click for more info](bugDetails/S-2.md) |
| S-3    | Kwik (745fd4e2) | Specification violation ([CVE-2024-22590](https://nvd.nist.gov/vuln/detail/CVE-2024-22590)): Implementation without a state machine that enable overwriting of the client's transport parameters and cryptographic information. | [Click for more info](bugDetails/S-3.md) |
| S-4    | Kwik (745fd4e2) | Specification violation: Process CRYPTO frame in a 0-RTT packet. | [Click for more info](bugDetails/S-4.md) |
| M-1    | Kwik (745fd4e2) | Memory-corruption bug: Exceeds the operating system’s maximum number of memory map- pings for a single process (100,000) when receiving PING frame from 50,000 clients. | [Click for more info](bugDetails/M-1.md) |
| S-5    | Lsquic (1b113d19) | Specification violation ([CVE-2024-25678](https://nvd.nist.gov/vuln/detail/CVE-2024-25678)): Retention of the unused encryption keys (PSK configuration). | [Click for more info](bugDetails/S-5.md) |
| L-1    | Lsquic (v4.0.2) | Logic bug: Incorrect handling of re-transmission, leaving a half-opening connection on the client side (PSK configuration). | [Click for more info](bugDetails/L-1.md) |
| S-6    | MsQuic (5c070cdc) | Specification violation: Does not issue its initial_source_connection_id at the correct connection state. | [Click for more info](bugDetails/S-6.md) |
| M-2    | Neqo (aaabc1c1) | Memory-corruption bug: NULL pointer dereference at ```neqo-transport/src/path.rs:147``` when trying to get the primary path that is not initialized yet. | [Click for more info](bugDetails/M-2.md) |
| M-3    | Neqo (aaabc1c1) | Memory-corruption bug: Limited connections due to a hardcoded value in the library: ```target/debug/build/neqo-crypto-a4be3db97961b0ce/out/nspr/pr/src/io/prlayer.c:619```. | [Click for more info](bugDetails/M-3.md) |
| M-4    | Picoquic (d2f01093) | Memory-corruption bug: NULL pointer dereference due to incorrect pruning of re-transmission queue. | [Click for more info](bugDetails/M-4.md) |
| S-7    | Picoquic (d2f01093) | Specification violation: Retry token tied to retry_source_connection_id. | [Click for more info](bugDetails/S-7.md) |
| S-8    | PQUIC (841c8228) | Specification violation: Invalid original_destination_connection_id. | [Click for more info](bugDetails/S-8.md) |
| S-9    | PQUIC (841c8228) | Specification violation: Limitless active_connection_id_limit. | [Click for more info](bugDetails/S-9.md) |
| S-10   | PQUIC (841c8228) | Specification violation ([CVE-2024-25679](https://nvd.nist.gov/vuln/detail/CVE-2024-25679)): Retention of the unused encryption keys. | [Click for more info](bugDetails/S-10.md) |
| L-2    | PQUIC (841c8228) | Logic bug: Incorrect direction of pruning a double-linked re-transmission queue.  | [Click for more info](bugDetails/L-2.md) |
| M-5    | PQUIC (841c8228) | Memory-corruption bug: NULL pointer dereference when removing a new connection context. | [Click for more info](bugDetails/M-5.md) |
| M-6    | PQUIC (841c8228) | Memory-corruption bug:  Buffer overflow when processing frame type 0x30. | [Click for more info](bugDetails/M-6.md) 
| L-3    | PQUIC (841c8228) | Logic bug: Infinite loop when processing frame type 0xFF | [Click for more info](bugDetails/L-3.md) |
| S-11   | PQUIC (841c8228) | Specification violation: Does not send HANDSHAKE_DONE after the handshake is confirmed (PSK configuration). | [Click for more info](bugDetails/S-11.md) |
| S-12   | Quiche (24a959ab) | Specification violation: Client authentication bypass using an empty certificate. | [Click for more info](bugDetails/S-12.md) |
| S-13   | Quiche (24a959ab) | Specification violation: Do not discard all Initial packet with payload size less than 1200 bytes. | [Click for more info](bugDetails/S-13.md) |
| M-7    | Quiche4j (ea5effce) | Memory-corruption bug: Concurrent modification exception. | [Click for more info](bugDetails/M-7.md) |
| S-14   | Quiche4j (ea5effce) | Specification violation: Limitless active_connection_id_limit. | [Click for more info](bugDetails/S-14.md) |
| S-15   | Quant (511d91c3) | Specification violation: Incorrect handling of an initialPing message, then closes the connection. | [Click for more info](bugDetails/S-15.md) |
| S-16   | Quant (511d91c3) | Specification violation: Do not discard all Initial packet with payload size less than 1200 bytes. | [Click for more info](bugDetails/S-16.md) |
| S-17   | Quiwi (b7b5dadb) | Specification violation: Does not close the connection when the number of received NEW_CONNECTION_ID frames exceed the active_connection_id_limit. | [Click for more info](bugDetails/S-17.md) |
| M-8    | Quinn (4395b969 & 0af891e0) | Memory-corruption bug ([CVE-2023-42805](https://nvd.nist.gov/vuln/detail/CVE-2023-42805)): Unwrap() a None value when processing an unexpected frame. | [Click for more info](bugDetails/M-8.md) |
| S-18   | Quinn (4395b969 & 0af891e0) | Specification violation: Process CRYPTO frame in 0-RTT packet. |  [Click for more info](bugDetails/S-18.md) |
| S-19   | XQUIC (00f62288) | Specification violation: Retention of the unused encryption keys. | [Click for more info](bugDetails/S-19.md) |
| S-20   | XQUIC (00f62288) | Specification violation: Maintaining a number of active connection IDs that exceed the active_connection_id_limit. | [Click for more info](bugDetails/S-20.md) |
| S-21 to S-28   | Aioquic (239f99b8), LSQuic (1b113d19), Neqo (aaabc1c1), QQuic-go (f78683ab), Quinn (4395b969), Quiwi (b7b5dadb), S2n-quic (ec651875), XQUIC (00f62288) | Specification violation: Only discard the first Initial packets carried in a UDP datagram with a payload size smaller than the minimum allowed maximum datagram size of 1200 bytes. | [Click for more info](bugDetails/S-21toS-28.md) |
| S-29 to S-38   | Aioquic (239f99b8), Kwik (745fd4e2), MsQuic (5c070cdc), LSQuic (1b113d19), Quant (511d91c3), Quiche (24a959ab), Quic-go (f78683ab), Quiche4j (ea5effce), Quiwi (b7b5dadb), S2n-quic (ec651875) | Specification violation: Accept Handshake packet from an unmatched Destination Connection ID. | [Click for more info](bugDetails/S-29toS-38.md) |
| S-39 to S-44   | Lsquic (1b113d19), MsQuic (5c070cdc), Neqo (aaabc1c1), Quiche4j (ea5effce), Quinn (4395b969 & 0af891e0), XQUIC (00f62288) | Specification violation: Does not close the connection when receiving a packet without a frame. | [Click for more info](bugDetails/S-39toS-44.md) |