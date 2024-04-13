FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y python3-pip python3-dev pkg-config graphviz-dev \
    swig libgmp-dev autoconf libtool antlr3 wget curl gperf

RUN /usr/bin/python3 -m pip install --upgrade pip && \
    pip install pygraphviz && pip install scikit-umfpack && pip install pydot



WORKDIR /code

COPY /algorithm /code
COPY /dot-files /code/dot-files

RUN pip3 install -r requirements.txt
RUN pysmt-install --confirm-agreement --z3 
RUN pysmt-install --confirm-agreement --msat
# RUN pysmt-install --confirm-agreement --cvc4
# cvc4 configure error
RUN pysmt-install --confirm-agreement --yices 

RUN mkdir -p output

CMD [ "python3", "./main.py", "--ref=dot-files/bowling.dot", "--upd=dot-files/pong.dot", "-ooutput/out.dot"]
