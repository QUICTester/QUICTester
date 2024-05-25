# 🐛 Bugs Found

| Bug ID | Server | Description | Details |
| :----- | :----- | :---------- | :------------- |
| QT1    | Kwik (745fd4e2) | Specification violation ([CVE-2024-22588](https://nvd.nist.gov/vuln/detail/CVE-2024-22588)): Retention of the unused encryption keys. | [Click for more info](bugDetails/QT1.md) |
| QT2    | Kwik (745fd4e2) | Specification violation: Implementation without a state machine that enable overwriting of the client's transport parameters and cryptographic information. | [Click for more info](bugDetails/QT2.md) |
| QT3    | MsQuic (5c070cdc) | Specification violation: Does not issue its initial_source_connection_id at the correct connection state. | [Click for more info](bugDetails/QT3.md) |
| QT4    | Neqo (aaabc1c1) | Memory-corruption bug: NULL pointer dereference at ```neqo-transport/src/path.rs:147``` when trying to get the primary path that is not initialized yet. | [Click for more info](bugDetails/QT4.md) |
| QT5    | Neqo (aaabc1c1) | Memory-corruption bug: Limited connections due to a hardcoded value in the library: ```target/debug/build/neqo-crypto-a4be3db97961b0ce/out/nspr/pr/src/io/prlayer.c:619```. | [Click for more info](bugDetails/QT5.md) |
| QT6    | Picoquic (d2f01093) | Memory-corruption bug: NULL pointer dereference due to incorrect pruning of re-transmission queue. | [Click for more info](bugDetails/QT6.md) |
| QT7    | Picoquic (d2f01093) | Specification violation: Retry token tied to retry_source_connection_id. | [Click for more info](bugDetails/QT7.md) |
| QT8    | PQUIC (841c8228) | Specification violation: Invalid original_destination_connection_id. | [Click for more info](bugDetails/QT8.md) |
| QT9    | PQUIC (841c8228) | Specification violation: Limitless active_connection_id_limit. | [Click for more info](bugDetails/QT9.md) |
| QT10   | PQUIC (841c8228) | Specification violation ([CVE-2024-25679](https://nvd.nist.gov/vuln/detail/CVE-2024-25679)): Retention of the unused encryption keys. | [Click for more info](bugDetails/QT10.md) |
| QT11   | Quiche (24a959ab) | Specification violation: Client authentication bypass using an empty certificate. | [Click for more info](bugDetails/QT11.md) |
| QT12   | Quiche4j (ea5effce) | Memory-corruption bug: Concurrent modification exception. | [Click for more info](bugDetails/QT12.md) |
| QT13   | Quiche4j (ea5effce) | Specification violation: Limitless active_connection_id_limit. | [Click for more info](bugDetails/QT13.md) |
| QT14   | Quant (511d91c3) | Specification violation: Incorrect handling of an initialPing message, then closes the connection. | [Click for more info](bugDetails/QT14.md) |
| QT15   | Quiwi (b7b5dadb) | Specification violation: Does not close the connection when the number of received NEW_CONNECTION_ID frames exceed the active_connection_id_limit. | [Click for more info](bugDetails/QT15.md) |
| QT16   | XQUIC (00f62288) | Specification violation: Retention of the unused encryption keys. | [Click for more info](bugDetails/QT16.md) |
| QT17   | XQUIC (00f62288) | Specification violation: Maintaining a number of active connection IDs that exceed the active_connection_id_limit. | [Click for more info](bugDetails/QT17.md) |
| QT18   | PQUIC (841c8228) | Logic bug: Incorrect direction of pruning a double-linked re-transmission queue.  | [Click for more info](bugDetails/QT18.md) |
| QT19   | Quant (511d91c3) | Specification violation: Do not discard all Initial packet with payload size less than 1200 bytes. | [Click for more info](bugDetails/QT19.md) |
| QT20   | Quiche (24a959ab) | Specification violation: Do not discard all Initial packet with payload size less than 1200 bytes. | [Click for more info](bugDetails/QT20.md) |
| QT21   | PQUIC (841c8228) | Memory-corruption bug: NULL pointer dereference when removing a new connection context. | [Click for more info](bugDetails/QT21.md) |
| QT22 - QT29   | Aioquic, LSQUIC, Neqo, Quic-go, Quinn, Quiwi, S2n-quic, XQUIC | Specification violation: Only discard the first Initial packets carried in a UDP datagram with a payload size smaller than the minimum allowed maximum datagram size of 1200 bytes. | [Click for more info](bugDetails/QT22-29.md) |
| QT30   | LSQuic (1b113d19) | Specification violation: Accepts Handshake packet from an unmatched Destination Connection ID after the handshake is complete. | [Click for more info](bugDetails/QT30.md) |
| QT31 - QT38   | Kwik, MsQuic, Quant, Quiche, Quic-go, Quiche4j, Quiwi, S2n-quic | Specification violation: Accept Handshake packet from an unmatched Destination Connection ID until the handshake is complete. | [Click for more info](bugDetails/QT31-38.md) |
| QT39   | Quinn (4395b969 & 0af891e0) | Memory-corruption bug ([CVE-2023-42805](https://nvd.nist.gov/vuln/detail/CVE-2023-42805)): Unwrap() a None value when processing an unexpected frame. | [Click for more info](bugDetails/QT39.md) |
| QT40   | PQUIC (841c8228) | Memory-corruption bug:  Buffer overflow when processing frame type 0x30. | [Click for more info](bugDetails/QT40.md) |
| QT41   | PQUIC (841c8228) | Logic bug: Infinite loop when processing frame type 0xFF | [Click for more info](bugDetails/QT41.md) |
| QT42   | Aioquic (239f99b8) | Specification violation: Accept Handshake packet from an unmatched Destination Connection ID. | [Click for more info](bugDetails/QT42.md) |
| QT43   | Aioquic (239f99b8) | Specification violation: Does not close the connection when receiving an unexpected frame type | [Click for more info](bugDetails/QT43.md) |
| QT44   | Lsquic (1b113d19) | Specification violation: Does not close the connection when receiving a packet without a frame and still acknowledge the packet. | [Click for more info](bugDetails/QT44.md) |
| QT45   | Neqo (aaabc1c1) | Specification violation:  Does not close the connection when receiving a packet without a frame. | [Click for more info](bugDetails/QT45.md) |
| QT46   | Quiche4j (ea5effce) | Specification violation:  Does not close the connection when receiving a packet without a frame. | [Click for more info](bugDetails/QT46.md) |
| QT47   | XQUIC (00f62288) | Specification violation:  Does not close the connection when receiving a packet without a frame. | [Click for more info](bugDetails/QT47.md) |
| QT48   | Kwik (745fd4e2) | Memory-corruption bug: Exceeds the operating system’s maximum number of memory map- pings for a single process (100,000) when receiving PING frame from 50,000 clients. | [Click for more info](bugDetails/QT48.md) |
| QT49   | Kwik (745fd4e2) | Specification violation: Process CRYPTO frame in a 0-RTT packet. | [Click for more info](bugDetails/QT49.md) |
| QT50   | Lsquic (1b113d19) | Specification violation ([CVE-2024-25678](https://nvd.nist.gov/vuln/detail/CVE-2024-25678)): Retention of the unused encryption keys (PSK configuration). | [Click for more info](bugDetails/QT50.md) |
| QT51   | Lsquic (v4.0.2) | Logic bug: Incorrect handling of re-transmission, leaving a half-opening connection on the client side (PSK configuration). | [Click for more info](bugDetails/QT51.md) |
| QT52   | PQUIC (841c8228) | Specification violation: Does not send HANDSHAKE_DONE after the handshake is confirmed (PSK configuration). | [Click for more info](bugDetails/QT52.md) |
| QT53   | Quinn (4395b969 & 0af891e0) | Specification violation: Process CRYPTO frame in 0-RTT packet. |  [Click for more info](bugDetails/QT53.md) |
| QT54   | Quinn (4395b969 & 0af891e0) | Specification violation: Does not close the connection when receiving a packet without a frame. | [Click for more info](bugDetails/QT54.md) |
| QT55   | MsQuic (5c070cdc) | Specification violation: Does not close the connection when receiving a packet without a frame. | [Click for more info](bugDetails/QT55.md) |