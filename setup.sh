#!/bin/bash

sudo apt install python3 libssl-dev python3-dev python3-venv graphviz python-setuptools build-essential maven python3-tk cmake libgmp3-dev swig graphviz-dev swig3.0 gperf autoconf

cd quicMapper
python3 -m venv env
source env/bin/activate
python -m pip install --upgrade setuptools pip
python -m pip install -e .
python -m  pip install asgiref dnslib httpbin starlette wsproto --no-cache-dir
python -m  pip install pip install Werkzeug==2.0.3
python -m pip install "flask<2.2.0"
deactivate

cd ..
sudo apt install maven
git submodule update --init
git apply quicLearner/learnlib-py4j-example.patch
cd learnlib-py4j-example/java
mvn package

cd ../../quicLearner
mkdir run
python3 -m venv env
source env/bin/activate
python -m pip install --upgrade setuptools pip
python -m  pip install pydot pkg-resources py4j==0.10.9.7
deactivate

python3 -m pip install pygraphviz cython==0.29.23 scipy networkx pysmt pydot
pysmt-install --all