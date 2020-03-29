FROM ubuntu:18.04

EXPOSE 8080

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    python \
    python-pip \
    software-properties-common \
    supervisor

# Install Murmur from PPA.
RUN add-apt-repository ppa:mumble/release && \
    apt-get update && apt-get install -y mumble-server && \
    dpkg-reconfigure mumble-server

# Install ZeroC Ice.
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv B6391CB2CFBA643D && \
    apt-add-repository "deb http://zeroc.com/download/ice/3.7/ubuntu18.04 stable main" && \
    apt-get update && apt-get install -y python-zeroc-ice zeroc-ice-compilers

# Build Python app
RUN pip install -U pip
ADD requirements.txt /opt/murmur-rest/requirements.txt
RUN cd /opt/murmur-rest && pip install -r requirements.txt

# Add config files.
ADD ./etc/mumble-server.ini /etc/mumble-server.ini
ADD ./etc/supervisord.conf /etc/supervisor/supervisord.conf

# Add app.
ADD . /opt/murmur-rest

WORKDIR /opt/murmur-rest

# Mumble ports.
EXPOSE 50000

CMD ["/usr/bin/supervisord"]
