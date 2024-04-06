# QUICTester

### Total faults found: 54
- **43 specification violations** (An implemented behavior violates the QUIC specification.)
- **8 memory-related bugs** (An input causing a memory corruption and a server crash.)
- **3 logic flaws** (Incorrect logic implemented in code produces unexpected behavior.)

### Faults that are resolved after disclosure. 
![Faults found](/tables/faults.png)

### 19 QUIC implementations tested with 186 learned models
Basic: Basic handshake<br/>
Retry: Handshake with client address validation<br/>
ClientAuth: Handshake with client authentication<br/>
RetryClientAuth: Handshake with client address validation and authentication<br/>
PSK: Handshake with pre-shared key<br/>

![Faults found](/tables/implementationsTable.png)


