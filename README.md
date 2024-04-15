# QUICTESTER: Protocol Temporal-State Fuzzing for Analyzing QUIC Implementations
Learning-based fuzzing consists of 3 components, Learner, Mapper and the SUT (QUIC server). <br/>
Develop and test on Ubuntu 20.04 with Python3.8.

The fuzzing will consume quite many resources, consider:
- add ```ulimit -n 65536``` to .bashrc<br/>
- add ```ulimit -s 16384``` to .bashrc<br/>
- add ```vm.max_map_count=100000``` in ```/etc/sysctl.conf``` and run ```sysctl -p```
- disable whoopsie: ```systemctl stop whoopsie```<br/>

## Repository Organisation and Documentations
| Directory   | Description |
| :--------   | :--------   |
| findND      | Program that can reproduce and record any non-deterministic behaviour detected during learning. | 
| quicLearner | Source code for the Learner and results from the fuzzing.   | 
| quicMapper  | Source code for the Mapper, config file (inOutput.py) for the Learner and Mapper. |
| results     | Implementations tested, result tables and faults found |
| scripts     | Tools for automated analysis task. |
| secrets     | Certificate of CA, server and client; mapperSecrets.log for Wireshark decryption. |

## "Quic" start
- Install the Learner and Mapper using ```setup.sh```:<br/>
```./setup.sh```<br/>

## Manual Installation
### Mapper: QUIC-specific Test Harness (quicMapper/)
#### mapper.py
- Built from aioquic client library (https://github.com/aiortc/aioquic).
- Receive abstract input from the Learner and produce concrete input (valid QUIC packet).
- Send concrete input to the QUIC server.
- Receive concrete output from the QUIC server and extract its abstract output.
- Send the abstract output to the Learner.

- **Note: This can be used as a stand alone tool, see --sequence option in the help menu.**
- Requirements:
  - On Debian/Ubuntu run:<br/>
  ```sudo apt install libssl-dev python3-dev```
  - Setup client library in python virtual environment:<br/>
  ```cd quicMapper```<br/>
  ```python3 -m venv env```<br/>
  ```source env/bin/activate```<br/>
  ```python -m pip install -e .```<br/>
  ```python -m pip install asgiref dnslib httpbin starlette wsproto --no-cache-dir```<br/>
  ```python -m pip install Werkzeug==2.0.3```<br/>
  ```python -m pip install "flask<2.2.0"```<br/>
  ```deactivate```<br/>
  ```cd ..```<br/>
- See the help menu:<br/>
  ```cd quicMapper```<br/>
  ```env/bin/python mapper.py -help```<br/>
  ```cd ..```<br/>
- TLS decryption keys for Wireshark are in secrets/mapperSecrets.log

### Mapper Help Menu (Usage)
|  Arguments  | Description |
| :--------   | :--------   |
| &#8209;&#8209;sequence  | Only fuzz a list of input sequence defined in mapper.py (for manual testing, optional) | 
| -s / &#8209;&#8209;server   | Server to be tested (e.g., aioquic, google-quiche, kwik, lsquic, msquic, mvfst, neqo, ngtcp2, picoquic, pquic, quant, quiche, quiche4j, quic-go, quicly, quinn, quiwi, s2n-quic, xquic). | 
| &#8209;&#8209;cipher  | Cipher suite to use (e.g., AES_128_GCM_SHA256, AES_256_GCM_SHA384, CHACHA20_POLY1305_SHA256). |
| -p / &#8209;&#8209;port     | Mapper port (e.g., 5544). |
| -t / &#8209;&#8209;targetPort     | QUIC server port (e.g., 4433). |
| -c / &#8209;&#8209;cert     | Client certificate for client authentication (PEM file, optional). |
| -k / &#8209;&#8209;key      | Client key for client authentication (PEM file, optional). |
| &#8209;&#8209;invalidCertificate     | Invalid client certificate for client authentication (PEM file, optional). |
| &#8209;&#8209;caCert     | CA certificate for peer verification (PEM file, optional). |
| &#8209;&#8209;testRetryTokenExp     | Enable to test Retry token expiration (optional). |
| &#8209;&#8209;second     | Seconds to validate the Retry token, use with &#8209;&#8209;testRetryTokenExp (optional). |
| -r / &#8209;&#8209;run   | Command to run the QUIC server when &#8209;&#8209;testRetryToken is enabled (e.g., "python3 http3_server.py &#8209;&#8209;port 4431 &#8209;&#8209;certificate server-cert.pem &#8209;&#8209;private-key server-key.pem"). |
| &#8209;&#8209;secrets     | File to store the QUIC secrets (file, optional). |
| &#8209;&#8209;log     | Store Aioquic library log in file (file, optional). |
| -i / &#8209;&#8209;input | Dictionary that the Learner will use for fuzing (e.g., B ,BWR, BWCA, BWRCA) (for Learner).   | 
| &#8209;&#8209;count | Fuzzing iteration count of the Learner (for Learner).   | 
### Learner (quicLearner/)
#### learner.py
- Built from LearnLib (https://github.com/LearnLib/learnlib) and AALpy libraries (https://github.com/DES-Lab/AALpy).
- Generate abstract input.
- Receive abstract output.
- Learn and build the model of QUIC server.
- Requirements:
- To use LearnLib, you need to setup the Java Gateway Server (included in setup.sh) which required Maven to build the package:<br/>
  ```sudo apt install maven```<br/>
  ```git submodule update --init```<br/>
  ```git apply quicLearner/learnlib-py4j-example.patch```<br/>
  ```cd learnlib-py4j-example/java```<br/>
  ```mvn package```<br/>
  ```cd ../..```<br/>
- Setup AALpy and LearnLib library in python virtual environment:<br/>
  ```sudo apt install python3-tk```<br/>
  ```cd quicLearner```<br/>
  ```mkdir run```<br/>
  ```python3 -m venv env```<br/>
  ```source env/bin/activate```<br/>
  ```python -m pip install pydot pkg-resources py4j==0.10.9.7```<br/>
  ```deactivate```<br/>
  ```cd ..```<br/>
- See the help menu:<br/>
  ```cd quicLearner```<br/>
  ```env/bin/python learner.py -help```<br/>
  ```cd ..```<br/>
### Learner Help Menu (Usage)
|  Arguments  | Description |
| :-------------   | :--------   |
| -s / --server   | Server to be tested (e.g., aioquic, google-quiche, kwik, lsquic, msquic, mvsfst, neqo, ngtcp2, picoquic, pquic, quant, quiche, quiche4j, quic-go, quicly, quinn, quiwi, s2n-quic, xquic). | 
| -i / &#8209;&#8209;input | Dictionary that the Learner will use for fuzing (e.g., B ,BWR, BWCA, BWRCA).   | 
| &#8209;&#8209;config  | Handshake configuration of the server (e.g., B, BWR, BWCA, BWRCA). |
| -p / &#8209;&#8209;port     | Mapper port (e.g., 5544). |
| -t / &#8209;&#8209;targetPort     | QUIC server port (e.g., 4433). |
| -c / &#8209;&#8209;cert     | Client certificate for client authentication (PEM file, optional). |
| -k / &#8209;&#8209;key      | Client key for client authentication (PEM file, optional). |
| &#8209;&#8209;invalidCertificate     | Invalid client certificate for client authentication (PEM file, optional). |
| &#8209;&#8209;caCert     | CA certificate for peer verification (PEM file, optional). |
| &#8209;&#8209;secrets     | File to store the QUIC secrets (file, optional). |
| &#8209;&#8209;log     | Show mapper's log in terminal (optional). |
| &#8209;&#8209;learnlib     | Use LearnLib instead of AALPY. |
| -r / &#8209;&#8209;run     | Command to run the QUIC server (e.g., "python3 http3_server.py &#8209;&#8209;port 4431 &#8209;&#8209;certificate server-cert.pem &#8209;&#8209;private-key server-key.pem"). |

**Notes: The mapper will use the default certificate and private key in quic/secrets/clientCert/.**

## Example
### fuzzing aioquic (commit 239f99b8a3d4f5bc88cb280df765f35722cefe57)
### "QUIC" Run with docker file (require docker and at least 4 free CPU cores)
```cd dockerFile/aioquic/fuzz_aioquic```<br/>
```sudo docker compose build --no-cache```<br/>
```sudo docker compose up fuzz_aioquic_B -d```<br/>

### Build the server manually
github: https://github.com/aiortc/aioquic.git (look for dependencies here)
```mkdir quicServers```<br/>
```cd quicServers```<br/>
```git clone https://github.com/aiortc/aioquic.git aioquic```<br/>
```cd aioquic```<br/>
```git checkout 239f99b8a3d4f5bc88cb280df765f35722cefe57```<br/>
### Aioquic virtual environment installation (tested on Ubuntu 20.04)
```python3 -m venv env```<br/>
```source env/bin/activate```<br/>
```python -m pip install -e .```<br/>
```python -m pip install asgiref dnslib httpbin starlette wsproto --no-cache-dir```<br/>
```python -m pip install Werkzeug==2.0.3```<br/>
```python -m pip install "flask<2.2.0"```<br/>
```deactivate```<br/>
```cd ../..```<br/>

### Run
```cd quicLearner```<br/>
Fuzz Basic (default handshake) configuration with all possible input:<br/>
```setsid env/bin/python3 learner.py -s aioquic --config B -i BWRCA-s -p 3341 -t 4431 --learnlib -r "../quicServers/aioquic/env/bin/python ../quicServers/aioquic/examples/http3_server.py --port 4431 --certificate ../secrets/serverCert/server-cert.pem --private-key ../secrets/serverCert/server-key.pem -l ../secrets/aioquicServer.log" > run/learner_aio_BWRCA-CS_3341.log 2>&1 &```<br/>
Fuzz Basic with Retry (handshake with client address validation) configuration with all possible input:<br/>
```setsid env/bin/python3 learner.py -s aioquic --config BWR -i BWRCA-s -p 3342 -t 4432 --learnlib -r "../quicServers/aioquic/env/bin/python ../quicServers/aioquic/examples/http3_server.py --port 4432 --certificate ../secrets/serverCert/server-cert.pem --private-key ../secrets/serverCert/server-key.pem -l ../secrets/aioquicServer.log --retry" > run/learner_aio_BWRCA-CS_3342.log 2>&1 &```<br/>
Decryption keys for Wireshark are in secrets/aioquicServer.log or secrets/mapperSecrets.log<br/>

### Result
The result will be in the ```results/<serverName>Models/<serverName>-<serverConfig>-<inputDictionary>-<N>/``` directory after the fuzzing is completed. The fuzzing process typically lasts for several hours to days.<br/>
Files to analyse:
- optimisedLearnedModel.pdf (tools are provided in ```scripts/```)
- stat.txt (see if the server crashes during fuzzing)
<br/>


## Configurations needed to fuzz a new QUIC implementation
Currently, we support 19 QUIC implementations, to add new implementations, in quicMapper/inOutput.py:
- Add the server name, short timeout and long timeout to the ```Server``` class.
- Add the server name to the ```LIST``` in bottom of the ```Server``` class.
<br/>

In quicMapper/mapper.py:
- Add the server to the ```startConfigureMapper()``` function.
- For ```alpnProtocols```, ```allAlpn``` is used in default.

Once these are set, QUICTester is ready to fuzz a new QUIC server. Have fun!

## Extending the fuzzer / Adding new input to the fuzzer
Modify quicMapper/mapper.py and any relevant code (e.g. quicMapper/connection.py).<br/>
Then, in quicMapper/inOutput.py:
- Add the input symbol to ```Input``` class.
- Add output symbol to ```Output``` class (if any).
- Create a new dictionary with the new input in ```InputDictionary``` class.
- Create a string for the new input dictionary and add the new input dictionary to the ```args.input``` list in quicLearner/learner.py and quicMapper/mapper.py.
- Map the input dictionary string to the input dictionary in quicLearner/learner.py:main().
<br/>

<hr/>