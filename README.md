# QUICTester

### Total faults found: 53
- **43 specification violations** (An implemented behavior violates the QUIC specification.)
- **8 memory-related bugs** (An input causing a memory corruption and a server crash.)
- **2 logic flaws** (Incorrect logic implemented in code produces unexpected behavior.)

### Flaws that are resolved after disclosure. 
![Faults found](/tables/faults.png)

### 18 QUIC implementations tested with 171 learned models
Basic: Basic handshake<br/>
Retry: Handshake with client address validation<br/>
ClientAuth: Handshake with client authentication<br/>
RetryClientAuth: Handshake with client address validation and authentication<br/>
PSK: Handshake with pre-shared key<br/>

![Faults found](/tables/implementationsTable.png)


