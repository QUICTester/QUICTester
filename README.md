# 👾 QUICTESTER: Blackbox Protocol Fuzzer for QUIC Servers
Learning-based fuzzing consists of 3 components, the Learner, Mapper and SUT (QUIC server under test). <br/>
Development and testing performed on Ubuntu 20.04 with Python3.8. <br/>
We have identified 55 faults, with 3 CVEs assigned: [CVE-2023-42805](https://nvd.nist.gov/vuln/detail/CVE-2023-42805), [CVE-2024-25679](https://nvd.nist.gov/vuln/detail/CVE-2024-25679), [CVE-2024-25678](https://nvd.nist.gov/vuln/detail/CVE-2024-25678).

The fuzzing process will consume many resources. To ensure OS limits don't interfere, consider doing the following:
- add ```ulimit -n 65536``` to .bashrc<br/>
- add ```ulimit -s 16384``` to .bashrc<br/>
- add ```vm.max_map_count=100000``` in ```/etc/sysctl.conf``` and run ```sysctl -p```
- disable whoopsie: ```systemctl stop whoopsie```<br/><br/>

## 📂 Repository Organisation and Documentations
| Directory   | Description |
| :--------   | :--------   |
| dockerFile  | Docker files to fuzz all 19 QUIC implementations (with all security configurations). | 
| findND      | Program that can reproduce and record any non-deterministic behaviour detected during learning. | 
| quicLearner | Source code for the Learner and results from the fuzzing.   | 
| quicMapper  | Source code for the Mapper, config file (inOutput.py) for the Learner and Mapper. |
| results     | Faults summary with descriptions. |
| scripts     | Tools for automated analysis task. |
| secrets     | Certificate of CA, server and client; mapperSecrets.log for Wireshark decryption. |
<br/>

## ⚡ "Quic" start
- Install the Learner and Mapper using [setup.sh](setup.sh):<br/>
```bash 
./setup.sh
```
<br/>

## 💾 Manual Installation
### Mapper: QUIC-specific Test Harness (quicMapper/)
The Mapper is built from [Aioquic](https://github.com/aiortc/aioquic). It receives abstract inputs from the Learner, produces concrete inputs (valid QUIC packets) and sends concrete inputs to the QUIC server. Once it receives concrete outputs (responses) from the QUIC server, it extracts the abstract output and sends the abstract output to the Learner. **Note: The Mapper can be used as a stand alone tool, see --sequence option in the help menu.**

### Mapper Setup:
On Debian/Ubuntu, run the following:
```bash
sudo apt install libssl-dev python3-dev
cd quicMapper
python3 -m venv env
source env/bin/activate
python -m pip install -e .
python -m pip install asgiref dnslib httpbin starlette wsproto --no-cache-dir
python -m pip install Werkzeug==2.0.3
python -m pip install "flask<2.2.0"
deactivate
cd ..
```

### 📖 Mapper Help Menu (Usage)
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
| &#8209;&#8209;secrets     | File to store the QUIC secrets (file, optional). The TLS decryption keys for Wireshark are available in secrets/mapperSecrets.log |
| &#8209;&#8209;log     | Store Aioquic library log in file (file, optional). |
| -i / &#8209;&#8209;input | Dictionary that the Learner will use for fuzing (e.g., B ,BWR, BWCA, BWRCA) (for Learner).   | 
| &#8209;&#8209;count | Fuzzing iteration count of the Learner (for Learner).   | 

### Learner (quicLearner/)
The Learner is built from [LearnLib](https://github.com/LearnLib/learnlib) and [AALpy](https://github.com/DES-Lab/AALpy). It generates abstract inputs and receives abstract output. It is responsible for learning and building the models for the tested QUIC server.

### Learner Setup:
On Debian/Ubuntu, run the following:
```bash
sudo apt install maven python3-tk
git submodule update --init
git apply quicLearner/learnlib-py4j-example.patch
cd learnlib-py4j-example/java
mvn package
cd ../../quicLearner
mkdir run
python3 -m venv env
source env/bin/activate
python -m pip install pydot pkg-resources py4j==0.10.9.7
deactivate
cd ..
```

### 📖 Learner Help Menu (Usage)
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

**Notes: The Mapper will use the default certificate and private key in [secrets](secrets/clientCert/).**
<br/><br/>

## 💻 Example (Fuzzing Aioquic: commit 239f99b8)
The fuzzing can be either run inside Docker, or manually built and run. Docker files for fuzzing all 19 QUIC implementations are provided in [dockerFile](dockerFile/).

### "Quic" start via docker file (requires docker and at least 4 free CPU cores)
```bash 
cd dockerFile/aioquic/fuzz_aioquic
sudo docker compose build --no-cache
sudo docker compose up fuzz_aioquic_B
```

### Manual Build and Fuzz
```bash 
mkdir quicServers
cd quicServers
git clone https://github.com/aiortc/aioquic.git aioquic
cd aioquic
git checkout 239f99b8

#### Aioquic virtual environment installation (tested on Ubuntu 20.04)
python3 -m venv env
source env/bin/activate
python -m pip install -e .
python -m pip install asgiref dnslib httpbin starlette wsproto --no-cache-dir
python -m pip install Werkzeug==2.0.3
python -m pip install "flask<2.2.0"
deactivate
cd ../..

# Run
cd quicLearner
# Fuzz Basic (default handshake) configuration with short timeout (use "-i B-l" for long timeout and "-i B" for mixed timeout)
setsid env/bin/python3 learner.py -s aioquic --config B -i B-s -p 3341 -t 4431 --learnlib -r "../quicServers/aioquic/env/bin/python ../quicServers/aioquic/examples/http3_server.py --port 4431 --certificate ../secrets/serverCert/server-cert.pem --private-key ../secrets/serverCert/server-key.pem -l ../secrets/aioquicServer.log" > run/learner_aioquic_B-s_3341.log 2>&1 &
# Fuzz Basic with Retry (handshake with client address validation) configuration with short timeout (use "-i BWR-l" for long timeout and "-i BWR" for mixed timeout)
setsid env/bin/python3 learner.py -s aioquic --config BWR -i BWR-s -p 3342 -t 4432 --learnlib -r "../quicServers/aioquic/env/bin/python ../quicServers/aioquic/examples/http3_server.py --port 4432 --certificate ../secrets/serverCert/server-cert.pem --private-key ../secrets/serverCert/server-key.pem -l ../secrets/aioquicServer.log --retry" > run/learner_aioquic_BWR-s_3342.log 2>&1 &
```
Decryption keys for Wireshark are in secrets/aioquicServer.log or secrets/mapperSecrets.log<br/>

### 📑 Results
The results will be stored in the ```results/<serverName>Models/<serverName>-<serverConfig>-<inputDictionary>-<N>/``` directory after the fuzzing is completed. The fuzzing process typically lasts for several hours, or several days for some configurations.<br/>
Files to analyse:
- optimisedLearnedModel.pdf (tools are provided in ```scripts/```)
- stat.txt (for information on server crashes during fuzzing)
<br/><br/>

## 🔧 Configurations needed to fuzz a new QUIC implementation
Currently, we support 19 QUIC implementations, to add new implementations, in [quicMapper/inOutPut.py](quicMapper/inOutPut.py):
- Add the server name, short timeout and long timeout to the ```Server``` class.
- Add the server name to the ```LIST``` in bottom of the ```Server``` class.
<br/>

In [quicMapper/mapper.py](quicMapper/mapper.py):
- Add the server to the ```startConfigureMapper()``` function.
- For ```alpnProtocols```, ```allAlpn``` is used in default.

Once these are set, QUICTester is ready to fuzz a new QUIC server. Have fun! <br/><br/>

## 🔨 Extending the fuzzer / Adding new input to the fuzzer
Modify [quicMapper/mapper.py](quicMapper/mapper.py) and any relevant code (e.g. [connection.py](quicMapper/src/aioquic/quic/connection.py)).<br/>
Then, in [quicMapper/inOutPut.py](quicMapper/inOutPut.py):
- Add the input symbol to ```Input``` class.
- Add output symbol to ```Output``` class (if any).
- Create a new dictionary with the new input in ```InputDictionary``` class.
- Create a string for the new input dictionary and add the new input dictionary to the ```args.input``` list in quicLearner/learner.py and quicMapper/mapper.py.
- Map the input dictionary string to the input dictionary in [quicLearner/learner.py](quicLearner/learner.py):main().
<br/>

<hr/>
