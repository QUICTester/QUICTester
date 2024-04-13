## findND: Reproduce the Non-deterministic Behaviour Dectected during Fuzzing.

### Requirements
- tcpdump
- Mapper

### Build Instruction
```make all``` <br/>
```mkdir run```

### Usage
1) Start the QUIC server.
2) Run finND program: <br/> ```sudo ./findND <serverName> <mapperPort> <serverPort>```
3) Provide the input sequence to the input prompt. <br/> For example: ```['initPing', '[IncRetryTkn]', 'initPing', 'initConClose']```.

### Result
The program will stop when it detects non-determinisitc behaviour. You see the differences in ```capture.pcap``` and ```capture0.pcap```.

#### Note: 
Most of the main reason of non-determinisitc result is because the timeout assign to the Mapper is not long enough. Try to increase the timeout of the server you testing in ```quicMapper/inOutPut.py```.
