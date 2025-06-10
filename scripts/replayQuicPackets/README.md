# Simple QUIC Packets Extractor and Replayer
This program can extract client Initial packets from a pcap file and replay the Initial packets it extracts to a QUIC server.

## Build
```bash
make
```

## Example
To extract Initial packets from a pcap file:
```bash
./replayQuicPackets -x quic_init_ping_50000.pcap -o ping_50000.raw
```

To replay the packets from a raw file:
```bash
./replayQuicPackets -r ping_50000.raw -p 4433
```